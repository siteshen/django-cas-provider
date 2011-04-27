from django.conf import settings
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.urlresolvers import get_callable
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from forms import LoginForm
from models import ServiceTicket, LoginTicket


__all__ = ['login', 'validate', 'logout', 'service_validate']


INVALID_TICKET = 'INVALID_TICKET'
INVALID_SERVICE = 'INVALID_SERVICE'
INVALID_REQUEST = 'INVALID_REQUEST'
INTERNAL_ERROR = 'INTERNAL_ERROR'

ERROR_MESSAGES = (
    (INVALID_TICKET, u'The provided ticket is invalid.'),
    (INVALID_SERVICE, u'Service is invalid'),
    (INVALID_REQUEST, u'Not all required parameters were sent.'),
    (INTERNAL_ERROR, u'An internal error occurred during ticket validation'),
)


def login(request, template_name='cas/login.html', \
                success_redirect=settings.LOGIN_REDIRECT_URL,
                warn_template_name='cas/warn.html'):
    service = request.GET.get('service', None)
    if request.user.is_authenticated():
        if service is not None:
            if request.GET.get('warn', False):
                return render_to_response(warn_template_name, {
                    'service': service,
                    'warn': False
                }, context_instance=RequestContext(request))
            ticket = ServiceTicket.objects.create(service=service, user=request.user)
            return HttpResponseRedirect(ticket.get_redirect_url())
        else:
            return HttpResponseRedirect(success_redirect)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            service = form.cleaned_data.get('service')
            if service is not None:
                ticket = ServiceTicket.objects.create(service=service, user=user)
                success_redirect = ticket.get_redirect_url()
            return HttpResponseRedirect(success_redirect)
    else:
        form = LoginForm(initial={
            'service': service,
            'lt': LoginTicket.objects.create()
        })
    return render_to_response(template_name, {
        'form': form,
        'errors': form.get_errors()
    }, context_instance=RequestContext(request))


def validate(request):
    """Validate ticket via CAS v.1 protocol"""
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is not None and ticket_string is not None:
        #renew = request.GET.get('renew', True)
        #if not renew:
        # TODO: check user SSO session
        try:
            ticket = ServiceTicket.objects.get(ticket=ticket_string)
            assert ticket.service == service
            username = ticket.user.username
            ticket.delete()
            return HttpResponse("yes\n%s\n" % username)
        except:
            pass
    return HttpResponse("no\n\n")


def logout(request, template_name='cas/logout.html', auto_redirect=False):
    url = request.GET.get('url', None)
    if request.user.is_authenticated():
        auth_logout(request)
        if url and auto_redirect:
            return HttpResponseRedirect(url)
    return render_to_response(template_name, {'url': url}, \
                              context_instance=RequestContext(request))


def service_validate(request):
    """Validate ticket via CAS v.2 protocol"""
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is None or ticket_string is None:
        return _cas2_error_response(INVALID_REQUEST)

    try:
        ticket = ServiceTicket.objects.get(ticket=ticket_string)
    except ServiceTicket.DoesNotExist:
        return _cas2_error_response(INVALID_TICKET)

    if ticket.service != service:
        ticket.delete()
        return _cas2_error_response(INVALID_SERVICE)

    user = ticket.user
    ticket.delete()
    return _cas2_sucess_response(user)


def _cas2_error_response(code):
    return HttpResponse(u''''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
            <cas:authenticationFailure code="%(code)s">
                %(message)s
            </cas:authenticationFailure>
        </cas:serviceResponse>''' % {
            'code': code,
            'message': dict(ERROR_MESSAGES).get(code)
    }, mimetype='text/xml')


def _cas2_sucess_response(user):
    return HttpResponse(auth_success_response(user), mimetype='text/xml')


def auth_success_response(user):
    from attribute_formatters import CAS, NSMAP, etree

    response = etree.Element(CAS + 'serviceResponse', nsmap=NSMAP)
    auth_success = etree.SubElement(response, CAS + 'authenticationSuccess')
    username = etree.SubElement(auth_success, CAS + 'user')
    username.text = user.username

    if settings.CAS_CUSTOM_ATTRIBUTES_CALLBACK:
        callback = get_callable(settings.CAS_CUSTOM_ATTRIBUTES_CALLBACK)
        attrs = callback(user)
        if len(attrs) > 0:
            formater = get_callable(settings.CAS_CUSTOM_ATTRIBUTES_FORMATER)
            formater(auth_success, attrs)
    return unicode(etree.tostring(response, encoding='utf-8'), 'utf-8')
