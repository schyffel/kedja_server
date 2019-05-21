from json import dumps
from unittest import TestCase

from pyramid import testing
from pyramid.request import apply_request_extensions, Request
from transaction import commit
from webtest import TestApp

from kedja.resources.card import Card


class CardsAPIViewTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.wall')
        self.config.include('kedja.resources.collection')
        self.config.include('kedja.resources.card')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api.cards import ContainedCardsAPI
        return ContainedCardsAPI

    def _fixture(self):
        content = self.config.registry.content
        root = content('Root')
        root['wall'] = wall = content('Wall', rid=2)
        wall['collection'] = collection = content('Collection', rid=3)
        collection['card'] = content('Card', rid=4)
        return root

    def test_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 3
        request.matchdict['subrid'] = 4
        inst = self._cut(request, context=root)
        response = inst.get()
        self.assertIsInstance(response, Card)

    def test_put(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='PUT', body=body, matchdict={'rid': 3, 'subrid': 4})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.put()
        self.assertEqual(response.title, 'Hello world!')
        self.assertIsInstance(response, Card)

    def test_delete(self):
        root = self._fixture()
        request = testing.DummyRequest()
        apply_request_extensions(request)
        request.matchdict['rid'] = 3
        request.matchdict['subrid'] = 4
        inst = self._cut(request, context=root)
        response = inst.delete()
        self.assertIsInstance(response, dict)
        self.assertEqual(response, {'removed': 4})
        self.assertNotIn('card', root['wall']['collection'])

    def test_collection_get(self):
        root = self._fixture()
        request = testing.DummyRequest()
        request.matchdict['rid'] = 3
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_get()
        self.assertIsInstance(response, list)
        self.assertIn(root['wall']['collection']['card'], response)

    def test_collection_post(self):
        root = self._fixture()
        body = bytes(dumps({'title': 'Hello world!'}), 'utf-8')
        request = Request.blank('/', method='POST', body=body, matchdict={'rid': 3})
        request.registry = self.config.registry
        apply_request_extensions(request)
        inst = self._cut(request, context=root)
        response = inst.collection_post()
        self.assertIn(response, root['wall']['collection'].values())
        self.assertEqual(len(root['wall']['collection']), 2)


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
        self.config.include('kedja.views.api.cards')

    def _fixture(self, request):
        from kedja import root_factory
        root = root_factory(request)
        root['wall'] = request.registry.content('Wall', rid=2)
        root['wall']['collection'] = request.registry.content('Collection', rid=3)
        root['wall']['collection']['card'] = request.registry.content('Card', rid=4)
        commit()
        return root

    def test_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/collections/3/cards/4', status=200)
        self.assertEqual(response.json_body, {'data': {}, 'rid': 4, 'type_name': 'Card'})

    def test_put(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.put('/api/1/collections/3/cards/4', params=dumps({'title': 'Hello world!'}), status=200)
        self.assertEqual({"type_name": "Card", "rid": 4, "data": {"title": "Hello world!"}}, response.json_body)

    def test_delete(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.delete('/api/1/collections/3/cards/4', status=200)
        self.assertEqual({"removed": 4}, response.json_body)

    def test_collection_get(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        self._fixture(request)
        response = app.get('/api/1/collections/3/cards', status=200)
        self.assertEqual([{'data': {}, 'rid': 4, 'type_name': 'Card'}], response.json_body)

    def test_collection_post(self):
        wsgiapp = self.config.make_wsgi_app()
        app = TestApp(wsgiapp)
        request = testing.DummyRequest()
        apply_request_extensions(request)
        root = self._fixture(request)
        response = app.post('/api/1/collections/3/cards', params=dumps({'title': 'Hello world!'}), status=200)
        # Find the new object
        keys = list(root['wall']['collection'].keys())
        keys.remove('card')
        self.assertEqual(len(keys), 1)
        new_rid = int(keys[0])
        self.assertEqual({'data': {'title': 'Hello world!'}, 'rid': new_rid, 'type_name': 'Card'}, response.json_body)