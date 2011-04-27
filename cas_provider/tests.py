from cas_provider.models import ServiceTicket
from cas_provider.views import _cas2_sucess_response, _cas2_error_response, \
    INVALID_TICKET
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from urlparse import urlparse
from django.conf import settings


class ViewsTest(TestCase):

    fixtures = ['cas_users.json', ]

    def setUp(self):
        self.service = 'http://example.com/'


    def test_succeessful_login(self):
        response = self._login_user('root', '123')
        self._validate_cas1(response, True)

        response = self.client.get(reverse('cas_login'), {'service': self.service}, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].startswith('%s?ticket=' % self.service))

        response = self.client.get(reverse('cas_login'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].startswith('http://testserver/'))

        response = self.client.get(response['location'], follow=False)
        self.assertIn(response.status_code, [302, 200])

        response = self.client.get(reverse('cas_login'), {'service': self.service, 'warn': True}, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cas/warn.html')


    def _cas_logout(self):
        response = self.client.get(reverse('cas_logout'), follow=False)
        self.assertEqual(response.status_code, 200)


    def test_logout(self):
        response = self._login_user('root', '123')
        self._validate_cas1(response, True)

        self._cas_logout()

        response = self.client.get(reverse('cas_login'), follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_anonymous(), True)


    def test_broken_pwd(self):
        self._fail_login('root', '321')

    def test_broken_username(self):
        self._fail_login('notroot', '123')

    def test_nonactive_user_login(self):
        self._fail_login('nonactive', '123')

    def test_cas2_success_validate(self):
        response = self._login_user('root', '123')
        response = self._validate_cas2(response, True)
        user = User.objects.get(username=self.username)
        self.assertEqual(response.content, _cas2_sucess_response(user).content)

    def test_cas2_custom_attrs(self):
        settings.CAS_CUSTOM_ATTRIBUTES_CALLBACK = cas_mapping
        response = self._login_user('editor', '123')

        response = self._validate_cas2(response, True)
        self.assertEqual(response.content, '''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'''
            '''<cas:authenticationSuccess>'''
                '''<cas:user>editor</cas:user>'''
                '''<cas:attributes>'''
                    '''<cas:attraStyle>Jasig</cas:attraStyle>'''
                    '''<cas:group>editor</cas:group>'''
                    '''<cas:is_staff>True</cas:is_staff>'''
                    '''<cas:is_active>True</cas:is_active>'''
                    '''<cas:email>editor@exapmle.com</cas:email>'''
                '''</cas:attributes>'''
            '''</cas:authenticationSuccess>'''
        '''</cas:serviceResponse>''')

        self._cas_logout()
        response = self._login_user('editor', '123')
        settings.CAS_CUSTOM_ATTRIBUTES_FORMATER = 'cas_provider.attribute_formatters.ruby_cas'
        response = self._validate_cas2(response, True)
        self.assertEqual(response.content, '''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'''
            '''<cas:authenticationSuccess>'''
                '''<cas:user>editor</cas:user>'''
                '''<cas:attraStyle>RubyCAS</cas:attraStyle>'''
                '''<cas:group>editor</cas:group>'''
                '''<cas:is_staff>True</cas:is_staff>'''
                '''<cas:is_active>True</cas:is_active>'''
                '''<cas:email>editor@exapmle.com</cas:email>'''
            '''</cas:authenticationSuccess>'''
        '''</cas:serviceResponse>''')

        self._cas_logout()
        response = self._login_user('editor', '123')
        settings.CAS_CUSTOM_ATTRIBUTES_FORMATER = 'cas_provider.attribute_formatters.name_value'
        response = self._validate_cas2(response, True)
        self.assertEqual(response.content, '''<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'''
            '''<cas:authenticationSuccess>'''
                '''<cas:user>editor</cas:user>'''
                    '''<cas:attribute name="attraStyle" value="Name-Value"/>'''
                    '''<cas:attribute name="group" value="editor"/>'''
                    '''<cas:attribute name="is_staff" value="True"/>'''
                    '''<cas:attribute name="is_active" value="True"/>'''
                    '''<cas:attribute name="email" value="editor@exapmle.com"/>'''
            '''</cas:authenticationSuccess>'''
        '''</cas:serviceResponse>''')


    def test_cas2_fail_validate(self):
        for user, pwd in (('root', '321'), ('notroot', '123'), ('nonactive', '123')):
            response = self._login_user(user, pwd)
            self._validate_cas2(response, False)


    def _fail_login(self, username, password):
        response = self._login_user(username, password)
        self._validate_cas1(response, False)

        response = self.client.get(reverse('cas_login'), {'service': self.service}, follow=False)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('cas_login'), follow=False)
        self.assertEqual(response.status_code, 200)



    def _login_user(self, username, password):
        self.username = username
        response = self.client.get(reverse('cas_login'), {'service': self.service})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cas/login.html')
        form = response.context['form']
        service = form['service'].value()
        return self.client.post(reverse('cas_login'), {
            'username': username,
            'password': password,
            'lt': form['lt'].value(),
            'service': service
        }, follow=False)


    def _validate_cas1(self, response, is_correct=True):
        if is_correct:
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.has_header('location'))
            location = urlparse(response['location'])
            ticket = location.query.split('=')[1]

            response = self.client.get(reverse('cas_validate'), {'ticket': ticket, 'service': self.service}, follow=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(unicode(response.content), u'yes\n%s\n' % self.username)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['form'].errors), 1)

            response = self.client.get(reverse('cas_validate'), {'ticket': 'ST-12312312312312312312312', 'service': self.service}, follow=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, u'no\n\n')


    def _validate_cas2(self, response, is_correct=True):
        if is_correct:
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.has_header('location'))
            location = urlparse(response['location'])
            ticket = location.query.split('=')[1]

            response = self.client.get(reverse('cas_service_validate'), {'ticket': ticket, 'service': self.service}, follow=False)
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['form'].errors), 1)

            response = self.client.get(reverse('cas_service_validate'), {'ticket': 'ST-12312312312312312312312', 'service': self.service}, follow=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, _cas2_error_response(INVALID_TICKET).content)
        return response


class ModelsTestCase(TestCase):

    fixtures = ['cas_users.json', ]

    def setUp(self):
        self.user = User.objects.get(username='root')

    def test_redirects(self):
        ticket = ServiceTicket.objects.create(service='http://example.com', user=self.user)
        self.assertEqual(ticket.get_redirect_url(), '%(service)s?ticket=%(ticket)s' % ticket.__dict__)


def cas_mapping(user):
    return {
        'is_staff': unicode(user.is_staff),
        'is_active': unicode(user.is_active),
        'email': user.email,
        'group': [g.name for g in user.groups.all()]
    }
