from json import dumps
from unittest import TestCase

from cornice import Errors
from pyramid import testing
from pyramid.request import apply_request_extensions, Request
from transaction import commit
from webtest import TestApp

from kedja.resources.wall import Wall


class ResourceAPIBaseTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.base import ResourceAPIBase
        return ResourceAPIBase

    def test_get_json_appstruct_no_payload(self):
        request = testing.DummyRequest()
        request.errors = Errors()
        request.registry = self.config.registry
        apply_request_extensions(request)
        view = self._cut(request)
        view.get_json_appstruct()
        self.assertEqual(len(request.errors), 1)
        # How should this be properly tested with cornice?

    def test_get_json_appstruct_bad_payload(self):
        request = Request.blank('/', body=b'Hello world!')
        request.errors = Errors()
        request.registry = self.config.registry
        apply_request_extensions(request)
        view = self._cut(request)
        view.get_json_appstruct()
        self.assertEqual(len(request.errors), 1)
        # How should this be properly tested with cornice?
