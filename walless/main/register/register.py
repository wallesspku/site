import uuid
import time
import random
from threading import Lock
import logging

from walless_utils import db, user_pool
from django.http import Http404

from ..models import User

reg_lock = Lock()
logger = logging.getLogger('walless')


def base36(length: int) -> str:
    # generate random strings
    assert length > 0
    alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    ret = []
    rng = random.Random(time.time())
    for _ in range(length):
        ret.append(rng.choice(alphabet))
    return ''.join(ret)


def register_user(email):
    with reg_lock:
        user_pool.pull(True)
        user = user_pool.email2user.get(email)
        if user is not None:
            if user.enable:
                logger.warning("User already in database and it has been enabled. Addition aborted.")
                return user
            else:
                db.en_dis_able_user(email, True)
                logger.warning("User (disabled) already in database and it is enabled now. Addition aborted.")
                return user
        username, domain = email.split('@')
        largest_id = max(user_pool.id2user)
        password = base36(8)
        tag = 'gfw:c'
        User(username=username, email=email, password=password, tag=tag, user_id=largest_id+1).save()
        logger.warning(f"Added user {email}.")
        user_pool.pull(True)
        return user_pool.email2user[email]


def reset_user(email, password):
    users = db.get_user_by_email(email)
    if len(users) == 0:
        raise Http404("User/Password Error")
    user = users[0]
    if user.password != password:
        raise Http404("User/Password Error")
    logger.info(f"User {user.email} just reset its password and uuid.")
    db.reset_user(email, password=base36(8), uuid=uuid.uuid4())
    return db.get_user_by_email(email)[0]
