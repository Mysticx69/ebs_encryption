# -*- coding: utf-8 -*-
"""
This script retrieves a list of unencrypted EBS volumes in the current AWS region.

It creates snapshots of these volumes, and then creates encrypted copies of those
snapshots using the specified KMS key ID.
The original unencrypted snapshots are
then deleted. The script requires the Boto3 library and valid AWS credentials.
"""
from typing import List
from typing import Optional
from typing import Tuple

import boto3


def get_instance_name(instance_id: str, ec2: boto3.client) -> Optional[str]:
    """Get the name of an EC2 instance using its instance ID."""
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response["Reservations"][0]["Instances"][0]

    if "Tags" not in instance:
        return None

    name_tag = next((tag for tag in instance["Tags"] if tag["Key"] == "Name"), None)
    return name_tag["Value"] if name_tag else None


def get_unencrypted_ebs_volumes(
    ec2: boto3.client,
) -> List[Tuple[str, str, Optional[str]]]:
    """Get a list of unencrypted EBS volumes and their associated instance IDs and names."""
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
                unencrypted_volumes.append(
                    (volume["VolumeId"], instance_id, instance_name)
                )

    return unencrypted_volumes[:1]


def create_snapshot(volume_id: str, ec2: boto3.client) -> str:
    """Create a snapshot of the specified EBS volume."""
    snapshot = ec2.create_snapshot(
        VolumeId=volume_id,
        Description=f"Snapshot for {volume_id} - Created by script (SecureTheCloud)",
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
    encrypted_snapshot = ec2.copy_snapshot(
        SourceRegion=current_region,
        SourceSnapshotId=snapshot_id,
        KmsKeyId=kms_key_id,
        Encrypted=True,
        Description=f"Encrypted snapshot copy for {volume_id} from {snapshot_id}",
    )
    encrypted_snapshot_id = encrypted_snapshot["SnapshotId"]

    if enable_fsr and fsr_availability_zones:
        ec2.enable_fast_snapshot_restores(
            AvailabilityZones=fsr_availability_zones,
            SourceSnapshotIds=[encrypted_snapshot_id],
        )
        print(
            f"Fast Snapshot Restore enabled for snapshot {encrypted_snapshot_id} in Availability Zones {', '.join(fsr_availability_zones)}"
        )

    return encrypted_snapshot_id


def stop_instance(instance_id: str, instance_name: str, ec2: boto3.client) -> None:
    """Stop the specified EC2 instance."""
    if instance_id:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Stopping instance {instance_id} ({instance_name})")
        waiter = ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} ({instance_name}) stopped")


def start_instance(instance_id: str, ec2: boto3.client) -> None:
    """Start the specified EC2 instance."""
    if instance_id:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Starting instance {instance_id}")
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} started")


def detach_volume(volume_id: str, ec2: boto3.client) -> None:
    """Detach the specified EBS volume."""
    response = ec2.detach_volume(VolumeId=volume_id)
    print(f'Detaching volume {volume_id} from instance {response["InstanceId"]}')
    waiter = ec2.get_waiter("volume_available")
    waiter.wait(VolumeIds=[volume_id])
    print(f"Volume {volume_id} detached")


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
    print(f"Creating encrypted volume {volume_id} from snapshot {snapshot_id}")
    waiter = ec2.get_waiter("volume_available")
    waiter.wait(VolumeIds=[volume_id])
    print(f"Encrypted volume {volume_id} created")
    return volume_id


def attach_volume(
    volume_id: str, instance_id: str, device: str, ec2: boto3.client
) -> None:
    """Attach the specified EBS volume to the specified instance."""
    ec2.attach_volume(VolumeId=volume_id, InstanceId=instance_id, Device=device)
    print(f"Attaching volume {volume_id} to instance {instance_id}")
    waiter = ec2.get_waiter("volume_in_use")
    waiter.wait(VolumeIds=[volume_id])
    print(f"Volume {volume_id} attached to instance {instance_id}")


def delete_snapshot(snapshot_id: str, ec2: boto3.client) -> None:
    """Delete the specified snapshot."""
    ec2.delete_snapshot(SnapshotId=snapshot_id)


def copy_tags(source_volume_id: str, target_volume_id: str, ec2: boto3.client) -> None:
    """Copy tags from the source EBS volume to the target EBS volume."""
    source_volume = ec2.describe_volumes(VolumeIds=[source_volume_id])["Volumes"][0]

    if "Tags" in source_volume:
        ec2.create_tags(Resources=[target_volume_id], Tags=source_volume["Tags"])
        print(
            f"Copied tags from volume {source_volume_id} to volume {target_volume_id}"
        )


def disable_fsr(
    snapshot_id: str, fsr_availability_zones: List[str], ec2: boto3.client
) -> None:
    """Disable Fast Snapshot Restore for the specified snapshot."""
    ec2.disable_fast_snapshot_restores(
        AvailabilityZones=fsr_availability_zones,
        SourceSnapshotIds=[snapshot_id],
    )
    print(
        f"Fast Snapshot Restore disabled for snapshot {snapshot_id} in Availability Zones {', '.join(fsr_availability_zones)}"
    )


def encrypt_ebs_volumes(kms_key_id: str) -> None:
    """Encrypt all unencrypted EBS volumes in the current region."""
    session = boto3.Session(profile_name="lzv1-ebs", region_name="eu-west-1")
    ec2 = session.client("ec2")
    unencrypted_volumes = get_unencrypted_ebs_volumes(ec2)
    print(unencrypted_volumes)

    for volume_id, instance_id, instance_name in unencrypted_volumes:
        print(
            f"Encrypting volume {volume_id} attached to instance {instance_id} ({instance_name})..."
        )

        stop_instance(instance_id, instance_name, ec2)

        snapshot_id = create_snapshot(volume_id, ec2)
        wait_for_snapshot(snapshot_id, ec2)

        volume_info = ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"][0]
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

        delete_snapshot(snapshot_id, ec2)
        print(
            f"Encrypted snapshot created for volume {volume_id}: {encrypted_snapshot_id}"
        )
        print(
            f"Unencrypted snapshot previously created for {volume_id} : {snapshot_id} has been deleted.  "
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
            attach_volume(encrypted_volume_id, instance_id, device, ec2)

        disable_fsr(encrypted_snapshot_id, fsr_availability_zones, ec2)
        start_instance(instance_id, ec2)

        print(f"Encryption process for volume {volume_id} completed")


if __name__ == "__main__":
    KMS_KEY_ID = "alias/aws/ebs"
    encrypt_ebs_volumes(KMS_KEY_ID)
    # session_test = boto3.Session(profile_name="lzv1-ebs", region_name="eu-west-1")
    # ec2_session = session_test.client("ec2")
    # test = get_unencrypted_ebs_volumes(ec2_session)
    # print(test)
