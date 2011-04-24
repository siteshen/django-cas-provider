from cas_provider.models import ServiceTicket
from cas_provider.views import _cas2_sucess_response, _cas2_error_response, \
    INVALID_TICKET
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from urlparse import urlparse


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


    def test_logout(self):
        response = self._login_user('root', '123')
        self._validate_cas1(response, True)

        response = self.client.get(reverse('cas_logout'), follow=False)
        self.assertEqual(response.status_code, 200)

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
        self._validate_cas2(response, True)

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
            self.assertEqual(response.content, _cas2_sucess_response(self.username).content)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['form'].errors), 1)

            response = self.client.get(reverse('cas_service_validate'), {'ticket': 'ST-12312312312312312312312', 'service': self.service}, follow=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, _cas2_error_response(INVALID_TICKET).content)


class ModelsTestCase(TestCase):

    fixtures = ['cas_users.json', ]

    def setUp(self):
        self.user = User.objects.get(username='root')

    def test_redirects(self):
        ticket = ServiceTicket.objects.create(service='http://example.com', user=self.user)
        self.assertEqual(ticket.get_redirect_url(), '%(service)s?ticket=%(ticket)s' % ticket.__dict__)

