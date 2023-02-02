#!/usr/bin/env python3
""" Verify integrity of local files by comparing checksum of local file with
remote S3 ETag.

Based on answers (mostly falsePockets') in this StackOverflow thread:
https://stackoverflow.com/questions/12186993/what-is-the-algorithm-to-compute-the-amazon-s3-etag-for-a-file-larger-than-5gb
"""
__author__ = "Fredrik Boulund"
__date__ = "2022"
from sys import argv, exit
from hashlib import md5
import argparse
import logging

import boto3

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-l", "--local-file", required=True,
            help="Path to local file.")
    parser.add_argument("-b", "--bucket", required=True,
            help="S3 bucket name (without s3:// prefix).")
    parser.add_argument("-k", "-o", "--key", "--object", dest="key", required=True,
            help="S3 object key.")
    parser.add_argument("-a", "--s3-access-key")
    parser.add_argument("-s", "--s3-secret-key")
    parser.add_argument("-e", "--s3-endpoint")
    
    if len(argv) < 2:
        parser.print_help()
        exit(1)

    return parser.parse_args()


def compare_local_to_s3(local_path, bucket, key, s3_access_key, s3_secret_key, s3_endpoint):
    session = boto3.session.Session()
    client = session.client(
            service_name="s3",
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint,
    )
    resp = client.head_object(Bucket=bucket, Key=key)
    remote_etag = resp['ETag']
    total_length = resp['ContentLength']
    single_part_upload = '-' not in remote_etag
    if single_part_upload:
        m = md5()
        with open(file, 'rb') as f:
            local_etag = f'"md5(f.read()).hexdigest()"'
        return local_etag == remote_etag
    else:
        # Get number of parts from S3 Etag 
        # (e.g. 3c012fb139f281318cd68061f0980f0e-134 has 134 parts)
        num_parts = int(remote_etag.strip('"').split('-')[-1])
        logger.debug(f"Parsed {num_parts=} from {remote_etag=}")

        md5s = []

        with open(local_path, 'rb') as f:
            size_read = 0
            for part_num in range(1,num_parts+1):
                resp = client.head_object(Bucket=bucket, Key=key, PartNumber=part_num)
                size_read += resp['ContentLength']
                local_data_part = f.read(resp['ContentLength'])
                assert len(local_data_part) == resp['ContentLength'] # sanity check
                md5s.append(md5(local_data_part))
        assert size_read == total_length, "Sum of part sizes doesn't equal total file size"
        digests = b''.join(m.digest() for m in md5s)
        digests_md5 = md5(digests)
        local_etag = f'"{digests_md5.hexdigest()}-{len(md5s)}"'
        return remote_etag == local_etag


if __name__ == "__main__":
    args = parse_args()
    file_ok = compare_local_to_s3(args.local_file, args.bucket, args.key, args.s3_access_key, args.s3_secret_key, args.s3_endpoint)
    if file_ok:
        print(f"{args.local_file} OK")

