from typing import List
import time
import logging
import datetime
import os
from argparse import ArgumentParser

from tqdm import tqdm
from walless_utils import db, EditReservior, User, db_setup, logger_setup, cfg

logger_setup(log_paths=[os.path.expanduser('~/.var/log/walless_cron.log')])
db_setup()
logger = logging.getLogger('walless')



def raise_balance(users: List[User], to_full=False):
    now = int(time.time())
    editor = EditReservior(
        sql=db.update_user_balance_sql, 
        db=db, block=True, cache_size=512
    )
    all_args = []
    for u in users:
        if to_full:
            new_balance = cfg['balance']['total'].get(u.grade, 20) * 2**30
        else:
            new_balance = max(0, u.balance) + cfg['balance']['daily'].get(u.grade, 2) * 2**30
        new_balance = min(new_balance, u.total_data)
        if new_balance == u.balance:
            continue
        # tuple: (balance, last_change, user_id)
        all_args.append((new_balance, now, u.user_id))
    for args in tqdm(all_args, desc='Updating balance'):
        editor.add(args)
    editor.flush()
    logger.warning('Balance updated. %d users updated. Time cost: %.2f', len(all_args), time.time()-now)


def daily_check():
    today = str(datetime.datetime.now().date())
    file_path = os.path.expanduser(os.path.join('~/.cache/walless_balance'))
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    need_refresh = False
    if os.path.exists(file_path):
        records = open(file_path).read().split('\n')
        if today > records[-1]:
            need_refresh = True
            records.append(today)
    else:
        records = [today]
        need_refresh = True
    with open(file_path, 'w') as fp:
        fp.write('\n'.join(records))
    return need_refresh


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-a', action='store_true', help='Fill to full.')
    parser.add_argument('-f', help='force to fill', action='store_true')
    args = parser.parse_args()
    all_users = db.all_users(enable_only=True)
    if args.f or args.a or daily_check():
        logger.info('Need update. Refreshing now.')
        raise_balance(all_users, args.a)
    else:
        logger.info('No need to update. Aborting.')
