from django.conf import settings
from django.contrib.auth import login as auth_login, \
    logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from forms import LoginForm
from models import ServiceTicket, LoginTicket


__all__ = ['login', 'validate', 'logout', 'service_validate']


INVALID_TICKET = 1
INVALID_SERVICE = 2
INVALID_REQUEST = 3

ERROR_MESSAGES = (
    (INVALID_TICKET, u'The provided ticket is invalid.'),
    (INVALID_SERVICE, u'Service is invalid'),
    (INVALID_REQUEST, u'Not all required parameters were sent.'),
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
        try:
            ticket = ServiceTicket.objects.get(ticket=ticket_string)
            username = ticket.user.username
            ticket.delete()
            return HttpResponse("yes\n%s\n" % username)
        except:
            pass
    return HttpResponse("no\n\n")


def logout(request, template_name='cas/logout.html'):
    url = request.GET.get('url', None)
    auth_logout(request)
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

    if settings.CAS_CHECK_SERVICE and ticket.service != service:
        ticket.delete()
        return _cas2_error_response(INVALID_SERVICE)

    username = ticket.user.username
    ticket.delete()
    return _cas2_sucess_response(username)


def _cas2_error_response(code):
    return HttpResponse(u''''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
            <cas:authenticationFailure code="%(code)s">
                %(message)s
            </cas:authenticationFailure>
        </cas:serviceResponse>''' % {
            'code': code,
            'message': dict(ERROR_MESSAGES).get(code)
    }, mimetype='text/xml')


def _cas2_sucess_response(username):
    return HttpResponse(u'''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
        <cas:authenticationSuccess>
            <cas:user>%(username)s</cas:user>
        </cas:authenticationSuccess>
    </cas:serviceResponse>''' % {'username': username}, mimetype='text/xml')
