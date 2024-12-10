from email import message_from_string
import re
import logging
from email.utils import parseaddr

import dkim

logger = logging.getLogger('walless')
email_pat = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')


class ValidationException(Exception):
    pass


def _parse_email(email_header: str):
    # remove empty lines
    # email_header = '\n'.join(filter(lambda z: z.strip() != '', email_header.split('\n')))
    email_header = email_header.strip()
    d = dkim.DKIM(email_header.encode())
    sig, include_headers, sig_headers = d.verify_headerprep(0)
    sig.pop(b'bh', None)
    if not d.verify_sig(sig, include_headers, sig_headers[0], dkim.get_txt):
        raise ValidationException("dkim")
    msg = message_from_string(email_header)
    sender, receiver = map(lambda z: parseaddr(z)[1], [msg.get(k) for k in ['From', 'To']])
    return sender.lower(), receiver.lower(), sig.get(b'd').decode()


def valid_receiver(email_addr):
    domain = email_addr.split('@')[1]
    for dom in [
        'pku.edu.cn', 'pku.org.cn', 'bjmu.edu.cn', 'tsinghua.edu.cn', 'jhu.edu', 'tsinghua.org.cn',
        'jhmi.edu', 'ruc.edu.cn', 'jh.edu',
    ]:
        if domain == dom or domain.endswith(dom):
            return True
    return False


def valid_sender(email_addr):
    return email_addr in [
        'do_not_reply@springernature.com', 'noreply@github.com'
    ]


def valid_domain(domain):
    return domain in ['springernature.com', 'notify.orcid.org']


def valid_email(header):
    try:
        sender, receiver, domain = _parse_email(header)
    except ValidationException as e:
        raise e
    except Exception as e:
        logger.error("Error when validating user. Exception: \n" + str(e))
        raise ValidationException('header')
    return sender, receiver, domain
