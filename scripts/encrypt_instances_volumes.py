# -*- coding: utf-8 -*-
# pylint: disable=W1203
# pylint: disable=W0718
"""This script encrypts all unencrypted EBS volumes for all EC2 instances."""
import logging
import time
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import botocore.exceptions


def setup_logging(log_file: str) -> logging.Logger:
    """
    Set up logging.

    Args:
        log_file: The file to write the logs to.

    Returns:
        The logger object.
    """
    logging.basicConfig(
        level=logging.INFO,
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def get_instance_name(instance: boto3.resource("ec2").Instance) -> Optional[str]:
    """
    Extract name from instance tags.

    Args:
        instance: The EC2 instance.

    Returns:
        The name of the instance, or None if no name is found.
    """
    for tag in instance.tags or []:
        if tag["Key"] == "Name":
            return tag["Value"]
    return "Name Unknown"


def get_volume_name(volume: 'boto3.resource("ec2").Volume') -> Optional[str]:
    """
    Extract the name from the volume tags.

    Args:
        volume: The boto3 Volume object.

    Returns:
        The name of the volume if found in the tags, otherwise None.
    """
    for tag in volume.tags or []:
        if tag["Key"] == "Name":
            return tag["Value"]
    return "Unknown Name"


def gather_unencrypted_info(
    ec2: boto3.resource,
) -> List[Tuple[str, str, List[Tuple[str, str]]]]:
    """
    Gather information about instances and their unencrypted volumes.

    Args:
        ec2: The boto3 EC2 resource object.

    Returns:
        A list of tuples, where each tuple contains the instance ID, the instance name,
        and a list of tuples with volume ID and volume name for unencrypted volumes attached to the instance.
    """
    unencrypted_info = []
    for instance in ec2.instances.all():
        unencrypted_volumes = []

        for volume in instance.volumes.all():
            if not volume.encrypted:
                volume_name = get_volume_name(volume)
                unencrypted_volumes.append((volume.id, volume_name))

        if unencrypted_volumes:
            instance_name = get_instance_name(instance)
            unencrypted_info.append((instance.id, instance_name, unencrypted_volumes))

    return unencrypted_info


def is_part_of_auto_scaling_group(instance_id: str, autoscaling) -> bool:
    """
    Check if an instance is part of an Auto Scaling group.

    Args:
        instance_id: The ID of the instance.
        autoscaling: The boto3 AutoScaling client object.

    Returns:
        True if the instance is part of an Auto Scaling group, False otherwise.
    """
    try:
        response = autoscaling.describe_auto_scaling_instances(
            InstanceIds=[instance_id]
        )
        return bool(response["AutoScalingInstances"])
    except botocore.exceptions.ClientError as error:
        logging.error(
            f"Failed to get Auto Scaling group for instance {instance_id}. Error: {error}"
        )
        return False


def encrypt_volumes(
    instance_id: str,
    ec2: boto3.resource,
    ec2_client: boto3.client,
    autoscaling: boto3.client,
    kms_key_id: str,
    logger: logging.Logger,
) -> None:
    """
    Encrypt all volumes associated with an instance.

    Args:
        instance_id: The ID of the instance.
        ec2: The boto3 EC2 resource object.
        kms_key_id: The ID of the KMS key to use for encryption.
        logger: The logger object.

    Returns:
        None
    """
    instance = ec2.Instance(instance_id)

    if is_part_of_auto_scaling_group(instance_id, autoscaling):
        logger.warning(
            f"Instance {instance.id} is part of an Auto Scaling group. Skipping..."
        )
        return

    if instance.instance_lifecycle == "spot":
        logger.warning(f"Instance {instance.id} is a Spot Instance. Skipping...")
        return

    instance_name = get_instance_name(instance)
    logger.info("#" * 45)
    logger.info("#         Processing the request...")
    logger.info("#" * 45)
    logger.info(
        f"Encrypting volume(s) attached to instance {instance.id} ({instance_name})..."
    )

    start_time = time.time()

    if instance.state["Name"] != "stopped":
        logger.info(f"1. Stopping instance {instance.id} ({instance_name})...")
        instance.stop()
        instance.wait_until_stopped()
        logger.info(f"Instance {instance.id} stopped.")

    else:
        logger.info(f"1. Instance {instance.id} ({instance_name}) already stopped.")

    for volume in instance.volumes.all():
        volume_name = get_volume_name(volume)

        if not volume.encrypted:
            logger.info(
                f"2. Creating snapshot of volume {volume.id} ({volume_name})..."
            )
            snapshot = ec2.create_snapshot(
                VolumeId=volume.id,
                Description="Created by SecureTheCloud script",
                TagSpecifications=[
                    {
                        "ResourceType": "snapshot",
                        "Tags": [
                            {
                                "Key": "Name",
                                "Value": f"Snapshot for volume {volume.id} ({volume_name})",
                            },
                        ],
                    },
                ],
            )
            snapshot.wait_until_completed()
            logger.info(f"Snapshot created: {snapshot.snapshot_id}.")

            logger.info(
                f"3. Copying snapshot {snapshot.snapshot_id} and encrypting it with KMS key ({kms_key_id})..."
            )
            encrypted_snapshot = ec2.Snapshot(
                snapshot.copy(
                    SourceRegion=instance.placement["AvailabilityZone"][:-1],
                    Encrypted=True,
                    KmsKeyId=kms_key_id,
                    Description="Encrypted snapshot created by SecureTheCloud script",
                    TagSpecifications=[
                        {
                            "ResourceType": "snapshot",
                            "Tags": [
                                {
                                    "Key": "Name",
                                    "Value": f"Encrypted Snapshot for volume {volume.id} ({volume_name})",
                                },
                            ],
                        },
                    ],
                )["SnapshotId"]
            )

            encrypted_snapshot.wait_until_completed()
            logger.info(
                f"Encrypted snapshot created for volume {volume.id} ({volume_name}): {encrypted_snapshot.snapshot_id}."
            )

            logger.info(
                f"Enabling Fast Snapshot Restore on {encrypted_snapshot.snapshot_id}..."
            )

            ec2_client.enable_fast_snapshot_restores(
                AvailabilityZones=[instance.placement["AvailabilityZone"]],
                SourceSnapshotIds=[encrypted_snapshot.snapshot_id],
            )

            snapshot.delete()
            logger.info(
                f"Unencrypted snapshot previously created for volume {volume.id} ({volume_name}): {snapshot.snapshot_id} has been deleted."
            )

            logger.info(
                f"4. Detaching volume {volume.id} ({volume_name}) from instance {instance.id} ({instance_name})..."
            )

            device_name = (
                volume.attachments[0]["Device"] if volume.attachments else None
            )

            volume.detach_from_instance(
                Device=device_name,
                InstanceId=instance_id,
                Force=True,
            )
            waiter = ec2.meta.client.get_waiter("volume_available")
            waiter.wait(VolumeIds=[volume.id])

            logger.info(f"Volume {volume.id} detached.")

            logger.info(
                f"5. Creating encrypted volume from snapshot {encrypted_snapshot.snapshot_id}..."
            )
            encrypted_volume = ec2.create_volume(
                AvailabilityZone=volume.availability_zone,
                SnapshotId=encrypted_snapshot.snapshot_id,
                KmsKeyId=kms_key_id,
                Encrypted=True,
            )

            waiter = ec2_client.get_waiter("volume_available")
            waiter.wait(VolumeIds=[encrypted_volume.id])

            logger.info(f"Encrypted volume {encrypted_volume.id} created.")

            logger.info(f"Disabling Fast Snapshot Restore on {snapshot.snapshot_id}...")

            ec2_client.disable_fast_snapshot_restores(
                AvailabilityZones=[instance.placement["AvailabilityZone"]],
                SourceSnapshotIds=[encrypted_snapshot.snapshot_id],
            )

            tags = (
                [{"Key": tag["Key"], "Value": tag["Value"]} for tag in volume.tags]
                if volume.tags
                else []
            )
            if tags:
                encrypted_volume.create_tags(Tags=tags)
                logger.info(
                    f"6. Copied tags from unencrypted volume {volume.id} ({volume_name}) to new encrypted volume {encrypted_volume.id}."
                )

            logger.info(
                f"7. Attaching new encrypted volume {encrypted_volume.id} to instance {instance.id} ({instance_name})..."
            )
            encrypted_volume.attach_to_instance(
                Device=device_name,
                InstanceId=instance_id,
            )
            waiter = ec2_client.get_waiter("volume_in_use")
            waiter.wait(VolumeIds=[encrypted_volume.id])

            logger.info(
                f"Volume {encrypted_volume.id} attached to instance {instance.id}."
            )

    logger.info(f"8. Starting instance {instance.id} ({instance_name})...")
    instance.start()
    instance.wait_until_running()
    logger.info(f"Instance {instance.id} started.")
    logger.info(
        f"Encryption process for instance {instance.id} ({instance_name}) completed."
    )


def main(profile_name: str, region_name: str, kms_key_id: str) -> None:
    """
    Entry point function to encrypt all volumes for all instances.

    Args:
        profile_name: The name of the AWS profile to use.
        region_name: The name of the AWS region to use.
        kms_key_id: The ID of the KMS key to use for encryption.

    Returns:
        None
    """
    logger = setup_logging("ebs_encryption.log")

    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    ec2 = session.resource("ec2")
    ec2_client = session.client("ec2")
    autoscaling = session.client("autoscaling")

    unencrypted_info = gather_unencrypted_info(ec2)
    print(unencrypted_info[:1])

    for instance_id, instance_name, _ in unencrypted_info[:1]:
        try:
            encrypt_volumes(
                instance_id, ec2, ec2_client, autoscaling, kms_key_id, logger
            )
        except Exception as error:
            logger.error(
                f"Failed to encrypt volumes for instance {instance_id} ({instance_name}). Error: {error}"
            )


if __name__ == "__main__":
    main("lzv1-ebs", "eu-west-1", "alias/aws/ebs")
