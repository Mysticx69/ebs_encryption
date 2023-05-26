# -*- coding: utf-8 -*-
"""Gather resources that need to be proccessed."""
import argparse
import configparser
import logging
import os
from typing import List
from typing import Tuple

import boto3
from encrypt_instances_volumes import gather_unencrypted_info

# pylint: disable=W1203
# pylint: disable=W0718
# pylint: disable=C0301


def setup_logging(log_file: str, log_dir: str) -> logging.Logger:
    """
    Set up logging.

    Args:
        log_file: The file to write the logs to.
        log_dir: The directory to create the log file in.

    Returns:
        The logger object.
    """
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(log_dir, log_file),
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def log_unencrypted_info(
    unencrypted_info: List[Tuple[str, str, List[Tuple[str, str, int]]]],
    logger: logging.Logger,
):
    """
    Log information about instances and their unencrypted volumes.

    Args:
        unencrypted_info: A list of tuples, where each tuple contains the instance ID, the instance name,
                          and a list of tuples with volume ID, volume name and volume size for unencrypted volumes
                          attached to the instance.
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
    # Read from the config file
    config = configparser.ConfigParser()
    config.read("../config.ini")

    # Extract the values
    region_name = config[profile_name]["region_name"]
    client_name = config[profile_name]["client_name"]

    logger = setup_logging(f"gather_instances_info_{client_name}.log", client_name)

    session = boto3.Session(profile_name=profile_name, region_name=region_name)
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
