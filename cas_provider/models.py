from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class ServiceTicket(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'))
    service = models.URLField(_('service'), verify_exists=False)
    ticket = models.CharField(_('ticket'), max_length=256)
    created = models.DateTimeField(_('created'), auto_now=True)

    class Meta:
        verbose_name = _('Service Ticket')
        verbose_name_plural = _('Service Tickets')

    def __unicode__(self):
        return "%s (%s) - %s" % (self.user.username, self.service, self.created)

class LoginTicket(models.Model):
    ticket = models.CharField(_('ticket'), max_length=32)
    created = models.DateTimeField(_('created'), auto_now=True)

    class Meta:
        verbose_name = _('Login Ticket')
        verbose_name_plural = _('Login Tickets')

    def __unicode__(self):
        return "%s - %s" % (self.ticket, self.created)
