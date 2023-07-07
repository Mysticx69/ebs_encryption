# EBS Gathering Infos Script

## Overview
This script is designed to gather information about all unencrypted EBS volumes attached to EC2 instances in your AWS account. It utilizes Amazon's Boto3 library to interact with AWS services. Please note that this script only gathers and logs information, it does not perform any actions on the instances or volumes.

## Requirements

Please use PipEnv to meet the requirements ! ([Pipenv Quick Start](README.md#3-using-pipenv-for-dependency-management))
- Python 3.7 or newer
- Pipenv
- AWS credentials configured

## Configuration
Create a `config.ini` file in the project root with the following format:

```ini
[profile_name]
region_name = your_region_name
client_name = your_client_name
```

Replace `profile_name`, `your_region_name`, and `your_client_name` with your own values.

- `profile_name`: The name of the AWS profile to use (credentials).
- `region_name`: The AWS region name.
- `client_name`: The name of the client.

## Usage
Run the script with the following command:

```bash
python3 scripts/gather_unencrypted_infos.py --profile your_profile_name
```

Replace `your_profile_name` with the name of the profile you want to use (this should match the profile_name you set in the config.ini file).

## Functionality
The script executes the following steps:

1. Reads the configuration file.
2. Sets up logging.
3. Creates a boto3 session.
4. Gathers information about instances and their unencrypted volumes.
5. Logs the gathered information.

## Description of Main Functions

The script contains several main functions, each fulfilling a specific purpose in the process:

- `setup_logging`: This function sets up logging.

- `read_config`: This function reads the configuration file.

- `create_session`: This function creates a boto3 session.

- `log_unencrypted_info`: This function logs information about instances and their unencrypted volumes.

- `main`: This is the entry point function to gather information about all volumes for all instances.

## Logging
All logs are written to a log file named `gather_instances_info_{client_name}.log` in the `client_name` directory. The `client_name` is the one you set in the config.ini file.

## Note
This script only gathers and logs information, it does not perform any actions on the instances or volumes. Always ensure you have the necessary permissions to access and interact with the AWS resources used in this script.
