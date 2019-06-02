from unittest import TestCase

from kedja.models.appmaker import root_populator
from pyramid import testing
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.request import apply_request_extensions


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
