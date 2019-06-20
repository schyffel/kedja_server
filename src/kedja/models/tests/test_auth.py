from unittest import TestCase

from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.request import apply_request_extensions
from zope.interface.verify import verifyObject

from kedja.interfaces import IOneTimeAuthToken, IOneTimeRegistrationToken, ICredentials
from kedja.models.appmaker import root_populator


class HTTPHeaderAuthenticationPolicyTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.user')
        self.config.include('kedja.resources.users')
        self.config.include('kedja.resources.credentials')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self, request):
        root = request.registry.content('Root')
        root_populator(root, request)
        cf = self.config.registry.content
        root['users']['10'] = user = cf('User', rid=10)
        cred = cf('Credentials', user, token='123')
        user.add_credentials(cred)
        return root, cred

    @property
    def _cut(self):
        from kedja.models.auth import HTTPHeaderAuthenticationPolicy
        return HTTPHeaderAuthenticationPolicy

    def test_remember(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        auth = self._cut(debug=True)
        auth.remember(request, '10', token='abc', root=root)
        user = root['users']['10']
        self.assertIn('abc', user.credentials)

    def test_forget(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        request.root = root
        request.headers['Authorization'] = cred.header()
        auth = self._cut(debug=True)
        auth.forget(request)
        user = root['users']['10']
        self.assertNotIn('123', user.credentials)

    def test_authenticated_userid(self):
        self.config.set_authorization_policy(ACLAuthorizationPolicy())
        self.config.set_authentication_policy(self._cut(debug=True))
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        request.root = root
        request.headers['Authorization'] = cred.header()
        self.assertEqual('10', request.authenticated_userid)


class OneTimeRegistrationTokenTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('kedja.utils')
        self.config.include('kedja.resources.root')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.auth import OneTimeRegistrationToken
        return OneTimeRegistrationToken

    def test_create(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = request.registry.content('Root')
        obj = self._cut(root)
        payload = {'hello': 'world'}
        temp_token = obj.create(payload, registry=self.config.registry)
        self.assertIsInstance(temp_token, str)

    def test_consume(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = request.registry.content('Root')
        obj = self._cut(root)
        payload = {'hello': 'world'}

        temp_token = obj.create(payload, registry=self.config.registry)
        result = obj.consume(temp_token)
        self.assertEqual(payload, result)

    def test_integration(self):
        self.config.include('kedja.models.auth')
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = request.registry.content('Root')
        obj = self.config.registry.queryAdapter(root, IOneTimeRegistrationToken)
        self.assertTrue(verifyObject(IOneTimeRegistrationToken, obj))


class OneTimeAuthTokenTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('kedja.utils')
        self.config.include('kedja.resources')

    def tearDown(self):
        testing.tearDown()

    def _fixture(self, request):
        root = request.registry.content('Root')
        root_populator(root, request)
        cf = self.config.registry.content
        root['users']['10'] = user = cf('User', rid=10)
        cred = cf('Credentials', user, token='123')
        user.add_credentials(cred)
        return root, cred

    @property
    def _cut(self):
        from kedja.models.auth import OneTimeAuthToken
        return OneTimeAuthToken

    def test_create(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self._cut(root)
        temp_token = obj.create(cred, registry=self.config.registry)
        self.assertIsInstance(temp_token, str)

    def test_consume(self):
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self._cut(root)
        temp_token = obj.create(cred, registry=self.config.registry)
        cred_returned = obj.consume('10', temp_token)
        self.assertTrue(ICredentials.providedBy(cred_returned))
        self.assertEqual(cred_returned, cred)

    def test_integration(self):
        self.config.include('kedja.models.auth')
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root, cred = self._fixture(request)
        obj = self.config.registry.queryAdapter(root, IOneTimeAuthToken)
        self.assertTrue(verifyObject(IOneTimeAuthToken, obj))
