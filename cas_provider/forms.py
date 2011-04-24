from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from models import LoginTicket
import datetime


__all__ = ['LoginForm', ]


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('username'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('password'))
    lt = forms.CharField(widget=forms.HiddenInput)
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self._user = None

    def clean_lt(self):
        ticket = self.cleaned_data['lt']
        timeframe = datetime.datetime.now() - \
                    datetime.timedelta(minutes=settings.CAS_TICKET_EXPIRATION)
        try:
            return LoginTicket.objects.get(ticket=ticket, created__gte=timeframe)
        except LoginTicket.DoesNotExist:
            raise ValidationError(_('Login ticket expired. Please try again.'))
        return ticket

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError(_('Incorrect username and/or password.'))
        if not user.is_active:
            raise ValidationError(_('This account is disabled.'))
        self._user = user
        self.cleaned_data.get('lt').delete()
        return self.cleaned_data

    def get_user(self):
        return self._user
    
    def get_errors(self):
        errors = []
        for k, error in self.errors.items():
            errors += [e for e in error]
        return errors
