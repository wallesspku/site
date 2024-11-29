from django.http import Http404, HttpResponse
from django.shortcuts import loader
import logging

from ..util import get_client_ip, setup_globals
from .backend import profile_info

logger = logging.getLogger('walless')


def profile(request, email, password):
    setup_globals()
    logger.info('Request of getting profile with email={}'.format(email))
    context = profile_info(email, password)
    if context is None:
        raise Http404
    context['ip'] = get_client_ip(request)
    template = loader.get_template('walless/profile.html')
    logger.info('Return profile page for {}'.format(email))
    return HttpResponse(template.render(context=context, request=request))
