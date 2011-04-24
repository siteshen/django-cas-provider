from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, \
    logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from forms import LoginForm
from models import ServiceTicket, LoginTicket
from utils import create_service_ticket


__all__ = ['login', 'validate', 'logout', 'service_validate']


def login(request, template_name='cas/login.html', success_redirect=getattr(settings, 'LOGIN_REDIRECT_URL', '/accounts/')):
    service = request.GET.get('service', None)
    if request.user.is_authenticated():
        if service is not None:
            ticket = create_service_ticket(request.user, service)
            if service.find('?') == -1:
                return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
            else:
                return HttpResponseRedirect(service + '&ticket=' + ticket.ticket)
        else:
            return HttpResponseRedirect(success_redirect)
    errors = []
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        service = request.POST.get('service', None)
        lt = request.POST.get('lt', None)

        try:
            login_ticket = LoginTicket.objects.get(ticket=lt)
        except:
            errors.append(_('Login ticket expired. Please try again.'))
        else:
            login_ticket.delete()
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    if service is not None:
                        ticket = create_service_ticket(user, service)
                        return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
                    else:
                        return HttpResponseRedirect(success_redirect)
                else:
                    errors.append(_('This account is disabled.'))
            else:
                    errors.append(_('Incorrect username and/or password.'))
    form = LoginForm(service)
    return render_to_response(template_name, {'form': form, 'errors': errors}, context_instance=RequestContext(request))


def validate(request):
    """Validate ticket via CAS v.1 protocol"""
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is not None and ticket_string is not None:
        try:
            ticket = ServiceTicket.objects.get(ticket=ticket_string)
            username = ticket.user.username
            ticket.delete()
            return HttpResponse("yes\r\n%s\r\n" % username)
        except:
            pass
    return HttpResponse("no\r\n\r\n")


def logout(request, template_name='cas/logout.html'):
    url = request.GET.get('url', None)
    auth_logout(request)
    return render_to_response(template_name, {'url': url}, context_instance=RequestContext(request))


def service_validate(request):
    """Validate ticket via CAS v.2 protocol"""
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is None or ticket_string is None:
        return _cas2_error_response(u'INVALID_REQUEST', u'Not all required parameters were sent.')

    try:
        ticket = ServiceTicket.objects.get(ticket=ticket_string)
    except ServiceTicket.DoesNotExist:
        return _cas2_error_response(u'INVALID_TICKET', u'The provided ticket is invalid.')

    if settings.CAS_CHECK_SERVICE and ticket.service != service:
        ticket.delete()
        return _cas2_error_response('INVALID_SERVICE', u'Service is invalid')

    username = ticket.user.username
    ticket.delete()
    return HttpResponse(u'''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
        <cas:authenticationSuccess>
            <cas:user>%(username)s</cas:user>
        </cas:authenticationSuccess>
    </cas:serviceResponse>''' % {'username': username}, mimetype='text/xml')


def _cas2_error_response(code, message):
    return HttpResponse(u''''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
            <cas:authenticationFailure code="%s">
                %s
            </cas:authenticationFailure>
        </cas:serviceResponse>''', mimetype='text/xml')
