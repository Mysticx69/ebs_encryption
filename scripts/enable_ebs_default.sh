#!/bin/bash

# Get the current EBS encryption status
ebs_encryption_status=$(aws ec2 get-ebs-encryption-by-default --region eu-west-1 --profile lzv1-ebs --query 'EbsEncryptionByDefault' --output text)

# If EBS encryption is not enabled, enable it
if [ "$ebs_encryption_status" = "False" ]; then
    aws ec2 enable-ebs-encryption-by-default --region eu-west-1 --profile lzv1-ebs
    echo "EBS encryption by default is now enabled."
else
    echo "EBS encryption by default is already enabled."
fi
