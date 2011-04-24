from django import forms
from django.utils.translation import ugettext_lazy as _
from utils import create_login_ticket


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('username'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('password'))
    #warn = forms.BooleanField(required=False)  # TODO: Implement
    lt = forms.CharField(widget=forms.HiddenInput, initial=create_login_ticket)

    def __init__(self, service=None, renew=None, gateway=None, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.request = request
        if service is not None:
            self.fields['service'] = forms.CharField(widget=forms.HiddenInput, initial=service)
