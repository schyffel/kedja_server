import os
from unittest import TestCase

from kedja.models.appmaker import root_populator
from pyramid import testing
from pyramid.request import apply_request_extensions, Request
from transaction import commit
from webtest import TestApp

from kedja.interfaces import IOneTimeRegistrationToken
from kedja.interfaces import IOneTimeAuthToken


class FunctionalAuthenticationAPITests(TestCase):
    """ Authentication tests post OAuth2 """

    def setUp(self):
        here = os.path.abspath(os.path.dirname(__file__))
        settings={
            'zodbconn.uri': 'memory://',
            'kedja.authomatic': os.path.join(here, 'authomatic.yaml')
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('arche.content')
        #self.config.include('arche.mutator')
        self.config.include('cornice')
        self.config.include('cornice_swagger')
        self.config.include('pyramid_zodbconn')
        self.config.include('pyramid_tm')
        self.config.include('kedja.models.auth')
        self.config.include('kedja.models.authomatic')
        self.config.include('kedja.resources')
        self.config.include('kedja.views.api.auth')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['users']['10'] = request.registry.content('User', rid=10)
        commit()
        return root

    def test_auth_methods(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get("/api/1/auth/methods")
        self.assertIn('google', response.json_body)

    def test_registraton(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        # Create registration token
        reg_tokens = self.config.registry.getAdapter(root, IOneTimeRegistrationToken)
        token = reg_tokens.create({'hello': 'world', 'provider': 'Google', 'id': 123})
        response = app.post("/api/1/auth/register/{}".format(token))
        self.assertIn('Authorization', response.json_body)

    def test_login_get_credentials(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        # Create login token
        credentials = self.config.registry.content('Credentials', root['users']['10'])
        commit()
        auth_tokens = self.config.registry.getAdapter(root, IOneTimeAuthToken)
        token = auth_tokens.create(credentials)
        response = app.post("/api/1/auth/credentials/{}/{}".format('10', token))
        self.assertIn('Authorization', response.json_body)