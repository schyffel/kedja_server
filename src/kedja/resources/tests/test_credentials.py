from unittest import TestCase

from pyramid import testing
from pyramid.authentication import extract_http_basic_credentials
from pyramid.authentication import HTTPBasicCredentials
from pyramid.request import apply_request_extensions


class HTTPHeaderAuthenticationPolicyTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.resources.credentials import Credentials
        return Credentials

    @property
    def _User(self):
        from kedja.resources.user import User
        return User

    def test_header(self):
        user = self._User(rid=1)
        obj = self._cut(user, token="123")
        self.assertEqual(obj.header(), "Basic MToxMjM=")

    def test_compat_with_pyramid(self):
        user = self._User(rid=1)
        obj = self._cut(user, token="123")
        request = testing.DummyRequest()
        request.headers['Authorization'] = obj.header()
        results = extract_http_basic_credentials(request)
        expected = HTTPBasicCredentials(username='1', password='123')
        self.assertIsInstance(results, HTTPBasicCredentials)
        self.assertEqual(results, expected)

    def test_json(self):
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources.user')
        #self.config.include('kedja.resources.credentials')
        user = self._User(rid=1)
        obj = self._cut(user, token="123")
        request = testing.DummyRequest()
        apply_request_extensions(request)
        results = obj.__json__(request)
        expected = {'type_name': 'User', 'rid': user.rid, 'data': {}, 'header':  obj.header()}
        self.assertEqual(results, expected)
