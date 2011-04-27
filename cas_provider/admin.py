from django.contrib import admin
from models import *


class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'created')
    list_filter = ('created',)

class LoginTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'created')
    list_filter = ('created',)

admin.site.register(ServiceTicket, ServiceTicketAdmin)
admin.site.register(LoginTicket, LoginTicketAdmin)
