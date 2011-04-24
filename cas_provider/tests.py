from django.core.urlresolvers import reverse
from django.test import TestCase
from urlparse import urlparse


class UserTest(TestCase):

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
            self.assertEqual(unicode(response.content), u'yes\r\n%s\r\n' % self.username if is_correct else u'no\r\n')
        else:
            self.assertEqual(response.status_code, 200)
            self.assertGreater(len(response.context['errors']), 0)
            self.assertEqual(len(response.context['form'].errors), 0)

