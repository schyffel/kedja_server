from json import dumps
from unittest import TestCase

from kedja.models.relations import RelationJSON
from pyramid import testing

from pyramid.request import apply_request_extensions, Request
from transaction import commit
from webtest import TestApp


class RelationsAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.relations import RelationsAPIView
        return RelationsAPIView

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = wall = content('Wall', title='Wall', rid=2)
        wall['collection'] = collection = content('Collection', rid=3)
        collection['cardA'] = content('Card', rid=10)
        collection['cardB'] = content('Card', rid=20)
        collection['cardC'] = content('Card', rid=30)
        return root

    def test_get(self):
        root = self._fixture()
        root['wall'].relations_map[1] = [10, 20]
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        request.matchdict['relation_id'] = 1
        inst = self._cut(request, context=root)
        response = inst.get()
        self.assertIsInstance(response, RelationJSON)
        self.assertEqual(dict(response), {'relation_id': 1, 'members': [10, 20]})

    def test_put(self):
        root = self._fixture()
        root['wall'].relations_map[1] = [10, 20]
        body = bytes(dumps({'members': [10, 20, 30]}), 'utf-8')
        request = Request.blank('/', method='PUT', body=body, matchdict={'rid': 2, 'relation_id': 1})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.put()
        self.assertEqual(dict(response), {'relation_id': 1, 'members': [10, 20, 30]})

    def test_delete(self):
        root = self._fixture()
        root['wall'].relations_map[1] = [10, 20]
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        request.matchdict['relation_id'] = 1
        inst = self._cut(request, context=root)
        response = inst.delete()
        self.assertEqual(response, {'removed': 1})

    def test_collection_get(self):
        root = self._fixture()
        root['wall'].relations_map[1] = [10, 20]
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 2
        inst = self._cut(request, context=root)
        response = inst.collection_get()
        expected_item = RelationJSON(1, members=(10, 20))
        self.assertIn(expected_item, response)

    def test_collection_post(self):
        root = self._fixture()
        body = bytes(dumps({'members': [20, 30]}), 'utf-8')
        request = Request.blank('/', method='POST', body=body, matchdict={'rid': 2})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_post()
        self.assertIsInstance(response, RelationJSON)
        relmap = root['wall'].relations_map
        self.assertEqual(len(relmap), 1)
        self.assertIn(response.relation_id, relmap)


class FunctionalCollectionsAPITests(TestCase):

    def setUp(self):
        settings={
            'zodbconn.uri': 'memory://'
        }
        self.config = testing.setUp(settings=settings)
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('cornice')
        self.config.include('cornice_swagger')
        self.config.include('pyramid_zodbconn')
        self.config.include('pyramid_tm')
        self.config.include('kedja.resources')
        self.config.include('kedja.views.api.relations')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        content = request.registry.content
        root['wall'] = wall = content('Wall', rid=2)
        root['wall']['collection'] = collection = content('Collection', rid=3)
        collection['cardA'] = content('Card', rid=10)
        collection['cardB'] = content('Card', rid=20)
        collection['cardC'] = content('Card', rid=30)
        wall.relations_map[1] = [10, 20]
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/relations/1', status=200)
        self.assertEqual(response.json_body, {'members': [10, 20], 'relation_id': 1})

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.put('/api/1/walls/2/relations/1', params=dumps({'members': [10, 20, 30]}), status=200)
        self.assertEqual({'members': [10, 20, 30], 'relation_id': 1}, response.json_body)

    def test_delete(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.delete('/api/1/walls/2/relations/1', status=200)
        self.assertEqual({"removed": 1}, response.json_body)

    def test_collection_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/walls/2/relations', status=200)
        self.assertEqual([{'members': [10, 20], 'relation_id': 1}], response.json_body)

    def test_collection_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        response = app.post('/api/1/walls/2/relations', params=dumps({'members': [10, 30]}), status=200)
        # Find the new object
        relmap = root['wall'].relations_map
        self.assertEqual(len(relmap), 2)
        keys = list(relmap.keys())
        keys.remove(1)
        new_relation_id = keys[0]
        self.assertEqual({'members': [10, 30], 'relation_id': new_relation_id}, response.json_body)