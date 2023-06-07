#!/bin/bash

# Check if the correct number of arguments was provided
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <aws_region> <aws_profile>"
    exit 1
fi

# Configuration
aws_region="$1"
aws_profile="$2"

# Get the current EBS encryption status
ebs_encryption_status=$(aws ec2 get-ebs-encryption-by-default --region "$aws_region" --profile "$aws_profile" --query 'EbsEncryptionByDefault' --output text)

# Check if the command was successful
if [[ $? -ne 0 ]]; then
    echo "Failed to get EBS encryption status."
    exit 1
fi

# If EBS encryption is not enabled, enable it
if [[ "$ebs_encryption_status" == "False" ]]; then
    aws ec2 enable-ebs-encryption-by-default --region "$aws_region" --profile "$aws_profile"

    # Check if the command was successful
    if [[ $? -ne 0 ]]; then
        echo "Failed to enable EBS encryption."
        exit 1
    fi

    echo "EBS encryption by default is now enabled."
else
    echo "EBS encryption by default is already enabled."
fi
