"""
Backup database. Clean old data to keep the database size small.
"""
import time
from typing import List
import os
from datetime import datetime, timedelta
from argparse import ArgumentParser
import logging
from pathlib import Path

from walless_utils import db, db_setup
from walless_utils.utils import (
    NODE_COLUMNS, USER_COLUMNS, tz, TRAFFIC_COLUMNS, REGISTRATION_COLUMNS,
    SUBLOG_COLUMNS,
)

logger = logging.getLogger('walless')


def save_csv(out_path: Path, columns: List[str], sql: str, args=None):
    """
    Save the result of the sql query to a csv file.
    """
    items = db.execute(sql, query=True, args=args)
    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(','.join(columns) + '\n')
        for item in items:
            f.write(','.join(map(str, item)) + '\n')


def iterate_save(out_dir: Path, columns: List[str], sql: str, use_ts: bool):
    # the sql takes one argument: the date or ts
    today = datetime.now(tz).date()
    cur = datetime(2024, 11, 21).date()
    while cur < today:
        file_name = cur.strftime('%y%m%d') + '.csv'
        if not os.path.exists(out_dir/file_name):
            if use_ts:
                start = datetime.combine(cur, datetime.min.time()).timestamp()
                args = (start, start + 86400)
            else:
                args = (cur,)
            save_csv(out_path=out_dir/file_name, columns=columns, sql=sql, args=args)
        cur += timedelta(days=1)


def main():
    parser = ArgumentParser()
    parser.add_argument('-o', type=str, help='Directory to save db backups.')
    args = parser.parse_args()
    out_dir = Path(args.o)

    db_setup()
    # probe table: delete records older than 2 days
    file_name = datetime.now().strftime('%y%m%d') + '.csv'
    # node and user table: save them to csv tables
    logger.warning('saving node table')
    save_csv(out_dir/'node'/file_name, NODE_COLUMNS, db.backup_node_sql)
    logger.warning('saving user table')
    save_csv(out_dir/'user'/file_name, USER_COLUMNS, db.backup_user_sql)
    # traffic table
    logger.warning('saving traffic table')
    iterate_save(out_dir/'traffic', TRAFFIC_COLUMNS, sql=db.backup_traffic_sql, use_ts=False)
    # sublog
    logger.warning('saving sublog table')
    iterate_save(out_dir/'sublog', SUBLOG_COLUMNS, sql=db.backup_sublog_sql, use_ts=True)
    # registration
    logger.warning('saving reg table')
    iterate_save(out_dir/'reg', REGISTRATION_COLUMNS, sql=db.backup_registration_sql, use_ts=True)
    # delete old records (2 days)
    logger.warning('cleaning probe table')
    db.execute(db.delete_probe_sql, args=(int(time.time()) - 86400*2,), query=False)
    # delete reg (7 days)
    logger.warning('cleaning reg table')
    db.execute(db.delete_registration_sql, args=(int(time.time()) - 86400*7,), query=False)
    # delete traffic (365 days)
    logger.warning('cleaning traffic table')
    db.execute(db.delete_traffic_sql, args=((datetime.now()-timedelta(days=365)).date()), query=False)
    # delete sublog (7 days)
    logger.warning('cleaning sublog table')
    db.execute(db.delete_sublog_sql, args=(int(time.time()) - 86400*7,), query=False)


if __name__ == '__main__':
    main()
