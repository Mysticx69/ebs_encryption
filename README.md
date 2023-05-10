
# Encrypt Unencrypted EBS Volumes

This script automates the process of creating encrypted copies of unencrypted Amazon EBS volumes. It does this by creating snapshots of the unencrypted volumes, encrypting the snapshots with a specified KMS key, and then creating new encrypted volumes from the encrypted snapshots.

## Requirements

- Python 3.6 or later
- Boto3 library
- Valid AWS credentials with necessary permissions

## Usage

1. Set up your AWS credentials as environment variables or configure them using the AWS CLI or AWS SDK.
2. Modify the `kms_key_id` variable in the `main()` function to use the desired KMS key for encryption.
3. Execute the script: `python3 scripts/script_encrypt_ebs.py`

## Function Descriptions

### get_instance_name(instance_id: str, ec2: boto3.client) -> Optional[str]

Returns the name of an EC2 instance given its instance ID.

### get_volume_name(volume_id: str, ec2: boto3.client) -> Optional[str]

Returns the name of an EBS volume given its volume ID.

### get_unencrypted_ebs_volumes(ec2: boto3.client) -> List[Tuple[str, str, Optional[str], Optional[str]]]

Retrieves a list of unencrypted EBS volumes and their associated instance IDs, names, and volume names.

### create_snapshot(volume_id: str, volume_name: str, ec2: boto3.client) -> str

Creates a snapshot of the specified EBS volume.

### wait_for_snapshot(snapshot_id: str, ec2: boto3.client) -> None

Waits for the specified snapshot to be completed.

### copy_snapshot_with_encryption(volume_id: str, snapshot_id: str, kms_key_id: str, ec2: boto3.client, enable_fsr: bool = False, fsr_availability_zones: Optional[List[str]] = None) -> str

Copies an existing snapshot with server-side encryption using the specified KMS key and optionally enables Fast Snapshot Restore.

### stop_instance(instance_id: str, instance_name: str, ec2: boto3.client) -> bool

Stops the specified EC2 instance.

### start_instance(instance_id: str, ec2: boto3.client) -> None

Starts the specified EC2 instance.

### detach_volume(volume_id: str, ec2: boto3.client) -> None

Detaches the specified EBS volume.

### create_encrypted_volume(snapshot_id: str, availability_zone: str, kms_key_id: str, ec2: boto3.client) -> str

Creates a new encrypted EBS volume from the specified snapshot.

### attach_volume(volume_id: str, instance_id: str, instance_name: str, device: str, ec2: boto3.client) -> None

Attaches the specified EBS volume to the specified instance.

### delete_snapshot(snapshot_id: str, ec2: boto3.client) -> None

Deletes the specified snapshot.

### copy_tags(source_volume_id: str, target_volume_id: str, ec2: boto3.client) -> None

Copies tags from the source EBS volume to the target EBS volume.

### disable_fsr(snapshot_id: str, fsr_availability_zones: List[str], ec2: boto3.client) -> None

Disables Fast Snapshot Restore for the specified snapshot.

### encrypt_ebs_volumes(kms_key_id: str) -> None

Encrypts all unencrypted EBS volumes in the current region.

### main() -> None

Entry point of the script.

## Notes

- This script should be used with caution as it stops and starts EC2 instances, which may cause downtime for your services.
- Always test it in a staging environment

## Steps

The script does the following:

1. Finds unencrypted EBS volumes and retrieves their instance IDs, names, and volume names.
2. Stops instances with unencrypted EBS volumes.
3. Creates snapshots of the unencrypted EBS volumes.
4. Waits for the snapshots to be completed.
5. Copies the snapshots and encrypts them using the specified KMS key.
6. Deletes the unencrypted snapshots.
7. Detaches the unencrypted EBS volumes.
8. Creates new encrypted EBS volumes from the encrypted snapshots.
9. Copies the tags from the unencrypted EBS volumes to the new encrypted EBS volumes.
10. Attaches the new encrypted EBS volumes to the instances.
11. Starts the instances.
12. Disables Fast Snapshot Restore (FSR) for the encrypted snapshots.
