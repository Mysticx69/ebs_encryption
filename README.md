# EBS Encryption Script

## Overview
This script is designed to encrypt all unencrypted EBS volumes attached to EC2 instances in your AWS account. It utilizes Amazon's Key Management Service (KMS) to ensure secure and reliable encryption. Please note that running this script can lead to service interruption as instances may need to be stopped and started during the encryption process.

## Requirements
- Python 3.7 or newer
- Boto3 library (`pip install boto3`)
- AWS credentials configured (either by setting environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, and `AWS_DEFAULT_REGION` or using AWS CLI's `configure` command)

## Configuration
Create a `config.ini` file in the same directory as the script with the following format:

```ini
[profile_name]
region_name = your_region_name
kms_key_id = your_kms_key_id
client_name = your_client_name
```

Replace `profile_name`, `your_region_name`, `your_kms_key_id`, and `your_client_name` with your own values.

- `profile_name`: The name of the AWS profile to use.
- `region_name`: The AWS region name.
- `kms_key_id`: The ID of the KMS key to use for encryption.
- `client_name`: The name of the client.

## Usage
Navigate to the script's directory and run the script with the following command:

```bash
python script_name.py --profile your_profile_name
```

Replace `script_name.py` with the actual name of the script file and `your_profile_name` with the name of the profile you want to use (this should match the profile_name you set in the config.ini file).

When you run the script, you'll be asked to confirm that you want to proceed since running the script can lead to service interruptions. Type 'y' or 'yes' to continue.

## Functionality
The script executes the following steps:

1. Gathers information about instances and their unencrypted volumes.
2. Checks if instances are part of an Auto Scaling group or are Spot Instances. If so, these instances are skipped.
3. For each instance that isn't part of an Auto Scaling group or a Spot Instance, it stops the instance (if it's not already stopped), creates snapshots of unencrypted volumes, copies and encrypts these snapshots with the specified KMS key, creates encrypted volumes from the encrypted snapshots, detaches the original unencrypted volumes, attaches the new encrypted volumes, and then restarts the instance.
4. It logs all activities and errors and presents a summary at the end.

## Logging
All logs are written to a log file named `ebs_encryption_{client_name}.log` in the `client_name` directory. The `client_name` is the one you set in the config.ini file.

## Warning
This script can cause service interruptions as it stops and starts instances during the encryption process. Always ensure you have recent backups of your data and thoroughly test this script in a non-production environment before using it in a production environment. Be sure to check that all services hosted on the instances are healthy after the script runs.
