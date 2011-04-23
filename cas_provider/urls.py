from django.conf.urls.defaults import *


urlpatterns = patterns('cas_provider.views',
    url(r'^login/?$', 'login', name='cas_login'),
    url(r'^validate/?$', 'validate', name='cas_validate'),
    url(r'^logout/?$', 'logout', name='cas_logout'),
)
