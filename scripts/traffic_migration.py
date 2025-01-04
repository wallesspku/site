import time
import os
import logging
from collections import defaultdict
import datetime
from dateutil import tz

from walless_utils import db, EditReservior, db_setup, logger_setup

logger_setup(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
db_setup()
logger = logging.getLogger("walless")


def batch(items: list, batch_size: int):
    cur = list()
    for i in items:
        cur.append(i)
        if len(cur) == batch_size:
            yield cur
            cur = list()
    if len(cur) > 0:
        yield cur


def go_over_all_traffic():
    # this function should be exclusive: should only be called by one process
    since = time.time()
    conn = db.connection()
    cur = conn.cursor()
    cur.execute(db.get_log_sql)
    all_traffic = cur.fetchall()
    logger.info(f'Reading all traffic. {len(all_traffic)} pieces in total.')
    # log_id, user_id, upload, download, log_time
    if len(all_traffic) == 0:
        return 0
    last_log_id = max([t[0] for t in all_traffic])
    cur.execute(db.delete_log_sql, (last_log_id,))

    data_record = defaultdict(lambda: [0, 0])
    # Balance, upload, download, time
    user_update = defaultdict(lambda: [0, 0, 0, 0])
    # upload, download
    node_update = defaultdict(lambda: [0, 0])
    all_servers = db.all_servers()
    uuid2node = {s.uuid: s for s in all_servers}

    # accumulate the traffic for (node, user, date) triples
    for log_id, user_id, node_uuid, u, d, log_time in all_traffic:
        if node_uuid not in uuid2node:
            continue
        node = uuid2node[node_uuid]
        date = datetime.datetime.fromtimestamp(log_time, tz=tz.gettz('Asia/Shanghai')).date()
        data_record[(date, user_id, node_uuid)][0] += u
        data_record[(date, user_id, node_uuid)][1] += d
        user_update[user_id][0] -= int((u+d)*node.weight)
        user_update[user_id][1] += u
        user_update[user_id][2] += d
        user_update[user_id][3] = max(user_update[user_id][3], log_time)
        node_update[node.uuid][0] += u
        node_update[node.uuid][1] += d

    # for traffic table, insert a new record if (node, user, date) does not exist
    # else update the record
    traffic_editor = EditReservior(
        sql=db.insert_or_update_traffic_sql, db=None, cursor=cur, cache_size=1024, block=True,
    )
    for (date, user_id, node_id), (u, d) in data_record.items():
        traffic_editor.add((
            date, user_id, node_id, 
            u, d, date, user_id, node_id,
            date, u, d, node_id, user_id
        ))
    traffic_editor.flush()

    # for user table, update the balance, upload, download, last_update_time
    user_editor = EditReservior(
        sql=db.update_user_sql, db=None, cursor=cur, cache_size=1024, block=True,
    )
    for user_id, (balance, u, d, ts) in user_update.items():
        user_editor.add((balance, u, d, ts, ts, user_id))
    user_editor.flush()

    # for node table, update the upload, download
    node_editor = EditReservior(
        sql=db.update_node_sql, db=None, cursor=cur, cache_size=1024, block=True,
    )
    for node_uuid, (u, d) in node_update.items():
        node_editor.add((u, d, node_uuid))
    node_editor.flush()

    cur.close()
    conn.commit()
    logger.warning(
        'Traffic migration done. '
        f'Found {len(all_traffic)} pieces. '
        f'Time: {time.time()-since:.2f}s'
    )


if __name__ == '__main__':
    go_over_all_traffic()
