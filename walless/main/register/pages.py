from django.http import HttpResponse, Http404
from django.shortcuts import loader
import logging
import traceback

from walless_utils import db

from ..util import email_pat, setup_globals
from .validate import valid_email, ValidationException, valid_domain, valid_receiver
from .register import register_user, reset_user
from ..constants import MAX_EMAIL_HEADER_LENGTH

logger = logging.getLogger('walless')


def verify_page(request):
    setup_globals()
    return HttpResponse(loader.get_template('walless/verify.html').render({}, request))


def success_page(request, user_email: str):
    user_info = register_user(user_email)
    context = {
        'clash_sub_url': user_info.clash_sub_url,
        'profile_url': user_info.profile_url
    }
    return HttpResponse(
        loader.get_template('walless/success.html').render(context, request=request)
    )


def error_page(request, error_type):
    if error_type == 'header':
        zh = '信头格式错误. 请确认您已经按照提示获取合法信头.'
        en = 'Cannot parse the uploaded email header. Please check if you followed the instructions.'
    elif error_type == 'receiver':
        zh = '请确认您使用了北京大学邮箱 (@pku.edu.cn, @*.pku.edu.cn, @bjmu.edu.cn).'
        en = 'Please check if you are using PKU email address.'
    elif error_type == 'sender':
        zh = '请确认您的邮件发件人是合法的. 注意我们只承认特定发件人的信头, 请不要随意选取收件箱的邮件.'
        en = 'Please verify that the sender of the selected email is accepted by Walless.'
    elif error_type == 'dkim':
        zh = '请确认您的信头没有被修改过!'
        en = 'Please verify the email header was not modified!'
    else:
        zh = '未知错误.'
        en = 'Unknown error.'
    return HttpResponse(loader.get_template('walless/verify.html').render({
        'error_msg_zh': zh, 'error_msg_en': en,
    }, request))


def verify_result_page(request):
    setup_globals()
    to_log = {'email_header': 'placeholder', 'sender': None, 'receiver': None}
    try:
        if 'header' not in request.POST:
            raise Http404
        header = request.POST.get('header')
        if len(header) < 128:
            raise ValidationException('header')
        sender, receiver, domain = valid_email(header)
        to_log.update({'sender': sender, 'receiver': receiver})
        if not valid_domain(domain):
            raise ValidationException('sender')
        if not valid_receiver(receiver):
            raise ValidationException('receiver')
        to_log['email_header'] = header[:MAX_EMAIL_HEADER_LENGTH-512]
        return_page = success_page(request, receiver)
        db.new_registration(**to_log, status='passed')
        logger.warning(f"{receiver} requested an account and passed DKIM verification.")
    except ValidationException as e:
        db.new_registration(**to_log, status=e.args[0])
        return_page = error_page(request, e.args[0])
    except Exception as e:
        db.new_registration(**to_log, status='unknown')
        logger.error('Unknown error: ' + str(e))
        logger.error(traceback.format_exc())
        return_page = error_page(request, 'unknown')
    return return_page


def direct_register(request, email: str):
    setup_globals()
    if not email_pat.findall(email):
        logger.error('Invalid email address.')
        raise Http404
    return success_page(request, email)


def reset_user_page(request, email: str, password: str):
    setup_globals()
    user = reset_user(email, password)
    context = {
        'clash_sub_url': user.clash_sub_url,
        'profile_url': user.profile_url
    }
    return HttpResponse(
        loader.get_template('walless/success.html').render(context, request=request)
    )
