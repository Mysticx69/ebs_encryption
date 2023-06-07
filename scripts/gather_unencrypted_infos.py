# -*- coding: utf-8 -*-
"""Gather resources that need to be proccessed."""
import argparse
import configparser
import logging
import os
import sys
from typing import List
from typing import Tuple

import boto3
import botocore.exceptions
from encrypt_instances_volumes import gather_unencrypted_info

# pylint: disable=W1203
# pylint: disable=W0718
# pylint: disable=C0301


CONFIG_FILE_PATH = "/home/ec2-user/encrypt-EBS/config.ini"


def setup_logging(client_name: str) -> logging.Logger:
    """
    Set up logging.

    Args:
        client_name: The name of the client, used to create the log file.

    Returns:
        The logger object.
    """
    # Create the log directory if it doesn't exist
    log_dir = f"/home/ec2-user/encrypt-EBS/{client_name}"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(log_dir, f"gather_instances_info_{client_name}.log"),
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def read_config() -> configparser.ConfigParser:
    """
    Read the configuration file.

    Returns:
        The configuration parser object.
    """
    # Check if the config file exists
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"Config file not found: {CONFIG_FILE_PATH}")
        sys.exit(1)

    # Read from the config file
    config = configparser.ConfigParser()

    try:
        config.read(CONFIG_FILE_PATH)
    except configparser.Error as error:
        print(f"Failed to read config file: {error}")
        sys.exit(1)

    return config


def create_session(profile_name: str, region_name: str) -> boto3.Session:
    """
    Create a boto3 session.

    Args:
        profile_name: The name of the AWS profile to use.
        region_name: The name of the AWS region to use.

    Returns:
        The boto3 session object.
    """
    try:
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
    except botocore.exceptions.ProfileNotFound as error:
        print(f"Failed to create boto3 session: {error}")
        sys.exit(1)

    return session


def log_unencrypted_info(
    unencrypted_info: List[Tuple[str, str, List[Tuple[str, str, int]]]],
    logger: logging.Logger,
):
    """
    Log information about instances and their unencrypted volumes.

    Args:
        unencrypted_info: A list of tuples, where each tuple contains the instance ID (str), the instance name (str),
                          and a list of tuples with volume ID (str), volume name (str) and volume size (int) for
                          unencrypted volumes attached to the instance. For example:
                          [
                            ("i-1234567890abcdef0", "Instance1", [
                              ("vol-049df61146f12f89d", "Volume1", 8),
                              ("vol-049df61146f12f89e", "Volume2", 10)
                            ]),
                            ("i-0987654321abcdef0", "Instance2", [
                              ("vol-049df61146f12f89f", "Volume3", 20)
                            ])
                          ]
        logger: The logger object to use for logging.

    Returns:
        None
    """
    logger.info("#" * 45)
    logger.info("#      Instances to be processed :")
    logger.info("#" * 45)
    logger.info("\n")

    for instance_id, instance_name, unencrypted_volumes in unencrypted_info:
        logger.info(
            f"{instance_id} ({instance_name}) with {len(unencrypted_volumes)} unencrypted volume(s) :"
        )
        for volume_id, volume_name, volume_size in unencrypted_volumes:
            logger.info(
                f"   Volume ID: {volume_id} | Volume Name: {volume_name} | Size: {volume_size} GB"
            )
        logger.info("-" * 45)


def main(profile_name: str) -> None:
    """
    Entry point function to encrypt all volumes for all instances.

    Args:
        profile_name: The name of the AWS profile to use.

    Returns:
        None
    """
    config = read_config()

    if profile_name not in config:
        print(f"Profile '{profile_name}' not found in config file")
        sys.exit(1)

    # Extract the values
    region_name = config[profile_name]["region_name"]
    client_name = config[profile_name]["client_name"]

    logger = setup_logging(client_name)

    session = create_session(profile_name, region_name)

    ec2 = session.resource("ec2")

    # Usage:
    infos = gather_unencrypted_info(ec2)
    log_unencrypted_info(infos, logger)


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Add argument for AWS profile
    parser.add_argument(
        "--profile", required=True, help="The name of the AWS profile to use."
    )

    # Parse arguments
    args = parser.parse_args()

    # Run the main function with the given profile
    main(args.profile)
