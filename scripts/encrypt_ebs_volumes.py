# -*- coding: utf-8 -*-
"""
This script retrieves a list of unencrypted EBS volumes in the current AWS region.

It creates snapshots of these volumes, and then creates encrypted copies of those
snapshots using the specified KMS key ID.
The original unencrypted snapshots are
then deleted. The script requires the Boto3 library and valid AWS credentials.
"""
import logging
import time
from typing import List
from typing import Optional
from typing import Tuple

import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError


LOG_FILE = "script_encrypt_ebs.log"

logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(console_handler)


logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)


def get_instance_name(instance_id: str, ec2: boto3.client) -> Optional[str]:
    """
    Get the name of an EC2 instance using its instance ID.

    Args:
        instance_id (str): The instance ID of the EC2 instance.
        ec2 (boto3.client): A boto3 EC2 client object.

    Returns:
        Optional[str]: The name of the EC2 instance or None if the name is not found.
    """
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response["Reservations"][0]["Instances"][0]

    if "Tags" not in instance:
        return "Name Unknown"

    name_tag = next((tag for tag in instance["Tags"] if tag["Key"] == "Name"), None)
    return name_tag["Value"] if name_tag else None


def get_volume_name(volume_id: str, ec2: boto3.client) -> Optional[str]:
    """
    Get the name of an EBS volume using its volume ID.

    Args:
        volume_id (str): The volume ID of the EBS volume.
        ec2 (boto3.client): A boto3 EC2 client object.

    Returns:
        Optional[str]: The name of the EBS volume or None if the name is not found.
    """
    response = ec2.describe_volumes(VolumeIds=[volume_id])
    volume = response["Volumes"][0]

    if "Tags" not in volume:
        return "Name Unknown"

    name_tag = next((tag for tag in volume["Tags"] if tag["Key"] == "Name"), None)
    return name_tag["Value"] if name_tag else None


def get_unencrypted_ebs_volumes(
    ec2: boto3.client,
) -> List[Tuple[str, str, Optional[str], Optional[str]]]:
    """Get a list of unencrypted EBS volumes and their associated instance IDs, names and volume names."""
    paginator = ec2.get_paginator("describe_volumes")
    unencrypted_volumes = []

    for page in paginator.paginate(
        Filters=[{"Name": "encrypted", "Values": ["false"]}]
    ):
        for volume in page["Volumes"]:
            if not volume.get("KmsKeyId") and volume["State"] == "in-use":
                instance_id = (
                    volume["Attachments"][0]["InstanceId"]
                    if volume["Attachments"]
                    else None
                )
                instance_name = (
                    get_instance_name(instance_id, ec2) if instance_id else None
                )
                volume_name = get_volume_name(volume["VolumeId"], ec2)
                unencrypted_volumes.append(
                    (volume["VolumeId"], instance_id, instance_name, volume_name)
                )

    return unencrypted_volumes[:4]


def create_snapshot(volume_id: str, volume_name: str, ec2: boto3.client) -> str:
    """Create a snapshot of the specified EBS volume."""
    logging.info("2. Creating snapshot of %s...", volume_id)
    snapshot = ec2.create_snapshot(
        VolumeId=volume_id,
        Description=f"Snapshot for {volume_id} ({volume_name}) - Created by script (SecureTheCloud)",
    )
    return snapshot["SnapshotId"]


def wait_for_snapshot(snapshot_id: str, ec2: boto3.client) -> None:
    """Wait for the specified snapshot to be completed."""
    waiter = ec2.get_waiter("snapshot_completed")
    waiter.wait(SnapshotIds=[snapshot_id])


def copy_snapshot_with_encryption(
    volume_id: str,
    snapshot_id: str,
    kms_key_id: str,
    ec2: boto3.client,
    enable_fsr: bool = False,
    fsr_availability_zones: Optional[List[str]] = None,
) -> str:
    """Copy an existing snapshot with server-side encryption using the specified KMS key and optionally enable Fast Snapshot Restore."""
    current_region = ec2.meta.region_name
    logging.info(
        "3. Copying snapshot %s and encrypting it with KMS key...", snapshot_id
    )
    encrypted_snapshot = ec2.copy_snapshot(
        SourceRegion=current_region,
        SourceSnapshotId=snapshot_id,
        KmsKeyId=kms_key_id,
        Encrypted=True,
        Description=f"Encrypted snapshot copy for {volume_id}",
    )
    encrypted_snapshot_id = encrypted_snapshot["SnapshotId"]

    if enable_fsr and fsr_availability_zones:
        ec2.enable_fast_snapshot_restores(
            AvailabilityZones=fsr_availability_zones,
            SourceSnapshotIds=[encrypted_snapshot_id],
        )
        logging.info(
            f"Fast Snapshot Restore (FSR) enabled for new snapshot %s in Availability Zone(s) {', '.join(fsr_availability_zones)}",
            encrypted_snapshot_id,
        )

    return encrypted_snapshot_id


def is_instance_managed_by_asg_or_spot(instance_id: str, ec2: boto3.client) -> bool:
    """Check if the specified EC2 instance is part of an Auto Scaling group or a Spot Instance."""
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response["Reservations"][0]["Instances"][0]

    if "InstanceLifecycle" in instance and instance["InstanceLifecycle"] == "spot":
        return True

    if "Tags" in instance:
        for tag in instance["Tags"]:
            if tag["Key"] == "aws:autoscaling:groupName":
                return True

    return False


def stop_instance(instance_id: str, instance_name: str, ec2: boto3.client) -> bool:
    """Stop the specified EC2 instance."""
    try:
        if is_instance_managed_by_asg_or_spot(instance_id, ec2):
            logging.warning(
                "Instance %s (%s) is part of an Auto Scaling group or a Spot Instance. Skipping...\n",
                instance_id,
                instance_name,
            )
            return False

        if instance_id:
            ec2.stop_instances(InstanceIds=[instance_id])
            logging.info("1. Stopping instance %s (%s)...", instance_id, instance_name)
            waiter = ec2.get_waiter("instance_stopped")
            waiter.wait(InstanceIds=[instance_id])
            logging.info("Instance %s (%s) stopped.", instance_id, instance_name)
        return True
    except ClientError as exceptclienterror:
        if exceptclienterror.response["Error"]["Code"] == "UnsupportedOperation":
            logging.warning(
                "Cannot stop instance %s (%s) due to UnsupportedOperation. Skipping...",
                instance_id,
                instance_name,
            )
            return False
        else:
            raise
    except WaiterError as exceptwaitererror:
        logging.error(
            f"Instance %s (%s) failed to stop: {exceptwaitererror}",
            instance_id,
            instance_name,
        )
        return False


def start_instance(instance_id: str, ec2: boto3.client) -> None:
    """Start the specified EC2 instance."""
    if instance_id:
        ec2.start_instances(InstanceIds=[instance_id])
        logging.info("8. Starting instance %s...", instance_id)
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        logging.info("Instance %s started.", instance_id)


def detach_volume(volume_id: str, ec2: boto3.client) -> None:
    """Detach the specified EBS volume."""
    response = ec2.detach_volume(VolumeId=volume_id)
    logging.info(
        f'4. Detaching volume %s from instance {response["InstanceId"]}...', volume_id
    )
    waiter = ec2.get_waiter("volume_available")
    waiter.wait(VolumeIds=[volume_id])
    logging.info("Volume %s detached", volume_id)


def create_encrypted_volume(
    snapshot_id: str, availability_zone: str, kms_key_id: str, ec2: boto3.client
) -> str:
    """Create a new encrypted EBS volume from the specified snapshot."""
    response = ec2.create_volume(
        SnapshotId=snapshot_id,
        AvailabilityZone=availability_zone,
        KmsKeyId=kms_key_id,
        Encrypted=True,
    )
    volume_id = response["VolumeId"]
    logging.info(
        "5. Creating encrypted volume %s from snapshot %s...", volume_id, snapshot_id
    )
    waiter = ec2.get_waiter("volume_available")
    waiter.wait(VolumeIds=[volume_id])
    logging.info("Encrypted volume %s created", volume_id)
    return volume_id


def attach_volume(
    volume_id: str, instance_id: str, instance_name: str, device: str, ec2: boto3.client
) -> None:
    """Attach the specified EBS volume to the specified instance."""
    ec2.attach_volume(VolumeId=volume_id, InstanceId=instance_id, Device=device)
    logging.info(
        "7. Attaching new encrypted volume %s to instance %s (%s)...",
        volume_id,
        instance_id,
        instance_name,
    )
    waiter = ec2.get_waiter("volume_in_use")
    waiter.wait(VolumeIds=[volume_id])
    logging.info("Volume %s attached to instance %s", volume_id, instance_id)


def delete_snapshot(snapshot_id: str, ec2: boto3.client) -> None:
    """Delete the specified snapshot."""
    ec2.delete_snapshot(SnapshotId=snapshot_id)


def copy_tags(source_volume_id: str, target_volume_id: str, ec2: boto3.client) -> None:
    """Copy tags from the source EBS volume to the target EBS volume."""
    source_volume = ec2.describe_volumes(VolumeIds=[source_volume_id])["Volumes"][0]
    logging.info(
        "6. Copied tags from unencrypted volume %s to new encrypted volume %s",
        source_volume_id,
        target_volume_id,
    )

    if "Tags" in source_volume:
        ec2.create_tags(Resources=[target_volume_id], Tags=source_volume["Tags"])


def disable_fsr(
    snapshot_id: str, fsr_availability_zones: List[str], ec2: boto3.client
) -> None:
    """Disable Fast Snapshot Restore for the specified snapshot."""
    ec2.disable_fast_snapshot_restores(
        AvailabilityZones=fsr_availability_zones,
        SourceSnapshotIds=[snapshot_id],
    )
    logging.info(
        f"Fast Snapshot Restore (FSR) disabled for snapshot %s in Availability Zone(s) {', '.join(fsr_availability_zones)}",
        snapshot_id,
    )


def encrypt_ebs_volumes(kms_key_id: str) -> None:
    """Encrypt all unencrypted EBS volumes in the current region."""
    session = boto3.Session(profile_name="lzv1-ebs", region_name="eu-west-1")
    ec2 = session.client("ec2")
    unencrypted_volumes = get_unencrypted_ebs_volumes(ec2)

    if not unencrypted_volumes:
        logging.info("No unencrypted EBS volumes found in the current region.")
        return

    for volume_id, instance_id, instance_name, volume_name in unencrypted_volumes:
        logging.info("#" * 45)
        logging.info("#         Processing the request...")
        logging.info("#" * 45)
        logging.info(
            "Encrypting volume %s (%s) attached to instance %s (%s)...",
            volume_id,
            volume_name,
            instance_id,
            instance_name,
        )

        start = time.time()

        stopped = stop_instance(instance_id, instance_name, ec2)
        if not stopped:
            continue

        snapshot_id = create_snapshot(volume_id, volume_name, ec2)
        wait_for_snapshot(snapshot_id, ec2)
        logging.info("Snapshot created : %s.", snapshot_id)

        volume_info = ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"][0]
        volue_size = volume_info["Size"]
        availability_zone = volume_info["AvailabilityZone"]
        enable_fsr = True
        fsr_availability_zones = [availability_zone]
        encrypted_snapshot_id = copy_snapshot_with_encryption(
            volume_id,
            snapshot_id,
            kms_key_id,
            ec2,
            enable_fsr=enable_fsr,
            fsr_availability_zones=fsr_availability_zones,
        )
        wait_for_snapshot(encrypted_snapshot_id, ec2)
        logging.info(
            "Encrypted snapshot created for volume %s: %s",
            volume_id,
            encrypted_snapshot_id,
        )

        delete_snapshot(snapshot_id, ec2)

        logging.info(
            "Unencrypted snapshot previously created for %s : %s has been deleted.",
            volume_id,
            snapshot_id,
        )

        device = (
            volume_info["Attachments"][0]["Device"]
            if volume_info["Attachments"]
            else None
        )

        detach_volume(volume_id, ec2)

        encrypted_volume_id = create_encrypted_volume(
            encrypted_snapshot_id, availability_zone, kms_key_id, ec2
        )

        copy_tags(volume_id, encrypted_volume_id, ec2)

        if instance_id and device:
            attach_volume(encrypted_volume_id, instance_id, instance_name, device, ec2)

        disable_fsr(encrypted_snapshot_id, fsr_availability_zones, ec2)
        start_instance(instance_id, ec2)

        end = time.time()
        time_sec = end - start

        processing_time = time.strftime("%H:%M:%S", time.gmtime(time_sec))

        logging.info("DONE. Encryption process for volume %s completed\n", volume_id)
        logging.info("#" * 45)
        logging.info("#         Summary information")
        logging.info("#" * 45)
        logging.info(
            "Unencrypted volume %s attached to %s (%s) has been processed.",
            volume_id,
            instance_id,
            instance_name,
        )
        logging.info("Processing time: %s", processing_time)
        logging.info("Volume Size : %s GB", volue_size)

        logging.info(
            "New volume encrypted : %s from snapshot %s.",
            encrypted_volume_id,
            encrypted_snapshot_id,
        )
        logging.info(
            "Instance %s (%s) started successfully.", instance_id, instance_name
        )
        logging.info(
            "Please make sure that all the services hosted on this machine are healthly!"
        )
        logging.info("-" * 45)
        logging.info("\n" * 2)


def main() -> None:
    """Start of the script."""
    kms_key_id = "alias/aws/ebs"
    encrypt_ebs_volumes(kms_key_id)


if __name__ == "__main__":
    main()
