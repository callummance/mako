#!/usr/bin/env python3

import os
import sys
import getopt
import subprocess
from datetime import datetime

from b2sdk.api import B2Api
from b2sdk.account_info.sqlite_account_info import SqliteAccountInfo

BACKUPS_DIR = "/tmp"


def dump_db(tgt_file: str, cluster_addr: str):
    subprocess.run(["rethinkdb-dump", "-c", cluster_addr,
                   "-f", tgt_file], check=True)


class B2Connection:
    def __init__(self, b2_key_id: str, b2_key: str, b2_bucket: str):
        # Setup B2 connection
        info = SqliteAccountInfo()
        b2api = B2Api(info)

        b2api.authorize_account(
            "production", b2_key_id, b2_key)

        self.bucket = b2api.get_bucket_by_name(b2_bucket)

    def backup_to_b2(self, cluster_addr: str, backup_prefix: str):
        # Make DB dump
        t = datetime.now()
        local_file_name = f'{backup_prefix}-{datetime.isoformat(t)}'
        local_file_path = f'{BACKUPS_DIR}/{local_file_name}'
        dump_db(local_file_path, cluster_addr)

        # Upload file to B2
        remote_file_name = f'{backup_prefix}/{datetime.isoformat(t)}'
        print(f"Uploading database dump to {remote_file_name} on B2")
        self.bucket.upload_local_file(
            local_file=local_file_path,
            file_name=remote_file_name,
            file_infos={
                "backup_type": backup_prefix,
                "backup_timestamp": str(t.timestamp())
            }
        )

        # Delete local file
        subprocess.run(["rm", "-rf", local_file_path])

    def remove_old_backups(self, backup_prefix: str, limit: int = 1):
        # Get list of existing backups
        print("Checking for old backups to remove...")
        old_backups = list(self.bucket.ls(backup_prefix))
        if len(old_backups) > limit:
            # We have more backups stored than is allowed, so work out the difference and delete the oldest
            no_to_delete: int = len(old_backups) - limit
            print(f"{no_to_delete} backups will now be removed")
            old_backups.sort(key=lambda b: b[0].file_info["backup_timestamp"])
            for file_version_to_delete, folder_name in old_backups[:no_to_delete]:
                try:
                    print(
                        f"Deleting backup {file_version_to_delete.file_name}...")
                    self.bucket.delete_file_version(
                        file_version_to_delete.id_, file_version_to_delete.file_name)
                    print("done.")
                except Exception as e:
                    print(
                        f"Failed to delete old backup due to exception {e}")


if __name__ == "__main__":
    b2_key_id = os.getenv("B2_KEY_ID")
    b2_key = os.getenv("B2_KEY")
    b2_bucket = os.getenv("B2_BUCKET")

    conn = B2Connection(b2_key_id, b2_key, b2_bucket)

    daily_backups_cnt = int(os.getenv("DAILY_BACKUPS"))
    weekly_backups_cnt = int(os.getenv("WEEKLY_BACKUPS"))

    cluster_addr = os.getenv("CLUSTER_ADDR")

    opts, args = getopt.getopt(sys.argv[1:], "dw")
    for opt, arg in opts:
        if opt == "-d":
            print(f"Taking a daily backup of the DB cluster at {cluster_addr}")
            conn.backup_to_b2(cluster_addr, "daily")
            conn.remove_old_backups("daily", daily_backups_cnt)
        elif opt == "-w":
            print(
                f"Taking a weekly backup of the DB cluster at {cluster_addr}")
            conn.backup_to_b2(cluster_addr, "weekly")
            conn.remove_old_backups("weekly", weekly_backups_cnt)
