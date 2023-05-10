# -*- coding: utf-8 -*-
"""Get unencrypted volume list with isntance ID + instance Name."""
import boto3
from encrypt_ebs_volumes import get_unencrypted_ebs_volumes


session = boto3.Session(profile_name="lzv1-ebs", region_name="eu-west-1")
ec2 = session.client("ec2")


ebs_list = get_unencrypted_ebs_volumes(ec2)
print(ebs_list)
