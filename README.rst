===================
django-cas-provider
===================

---------------------------------
Chris Williams <chris@nitron.org>
---------------------------------

OVERVIEW
=========

django-cas-provider is a provider for the `Central Authentication 
Service <http://jasig.org/cas>`_. It supports CAS version 1.0. It allows 
remote services to authenticate users for the purposes of 
Single Sign-On (SSO). For example, a user logs into a CAS server 
(provided by django-cas-provider) and can then access other services 
(such as email, calendar, etc) without re-entering her password for
each service. For more details, see the `CAS wiki <http://www.ja-sig.org/wiki/display/CAS/Home>`_
and `Single Sign-On on Wikipedia <http://en.wikipedia.org/wiki/Single_Sign_On>`_.

INSTALLATION
=============

To install, run the following command from this directory:

    	``python setup.py install``

Or, put cas_provider somewhere on your Python path.
	
USAGE
======

#. Add ``'cas_provider'`` to your ``INSTALLED_APPS`` tuple in *settings.py*.
#. In *settings.py*, set ``LOGIN_URL`` to ``'/cas/login/'`` and ``LOGOUT_URL`` to ``'/cas/logout/'``
#. In *urls.py*, put the following line: ``(r'^cas/', include('cas_provider.urls')),``
#. Create login/logout templates (or modify the samples)
#. Use 'cleanuptickets' management command to clean up expired tickets

SETTINGS
=========

CAS_TICKET_EXPIRATION - minutes to tickets expiration (default is 5 minutes)
CAS_CHECK_SERVICE - check if ticket service is equal with service GET argument

PROTOCOL DOCUMENTATION
=====================

* `CAS Protocol <http://www.jasig.org/cas/protocol>`
* `CAS 1 Architecture <http://www.jasig.org/cas/cas1-architecture>`
* `CAS 2 Architecture <http://www.jasig.org/cas/cas2-architecture>`
* `Proxy Authentication <http://www.jasig.org/cas/proxy-authentication>`
* `CAS – Central Authentication Service <http://www.jusfortechies.com/cas/overview.html>`
* `Proxy CAS Walkthrough <https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough>`

PROVIDED VIEWS
=============

login
---------

It has not required arguments.

Optional arguments:

* template_name - login form template name (default is 'cas/login.html')
* success_redirect - redirect after successful login if service GET argument is not provided 
   (default is settings.LOGIN_REDIRECT_URL)
* warn_template_name - warning page template name to allow login user to service if he
  already authenticated in SSO (default is 'cas/warn.html')

If request.GET has 'warn' argument - it shows warning message if user has already
authenticated in SSO instead of generate Service Ticket and redirect.

logout
-----------

This destroys a client's single sign-on CAS session. The ticket-granting cookie is destroyed, 
and subsequent requests to login view will not obtain service tickets until the user again
presents primary credentials (and thereby establishes a new single sign-on session).

It has not required arguments.

Optional arguments:

* template_name - template name for page with successful logout message (default is 'cas/logout.html')

validate
-------------

It checks the validity of a service ticket. It is part of the CAS 1.0 protocol and thus does
not handle proxy authentication.

It has not arguments. 

service_validate
-------------------------

It checks the validity of a service ticket and returns an XML-fragment response via CAS 2.0 protocol.
Work with proxy is not supported yet.

It has not arguments.


