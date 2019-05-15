from unittest import TestCase

import colander
from arche.content import ContentType
from arche.folder import Folder
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import apply_request_extensions

from kedja.resources.mixins import JSONRenderable
from webob.multidict import MultiDict


class DummySchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
    )


class Dummy(Folder, JSONRenderable):
    pass


class APIViewUnitTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources.root')
        DummyContent = ContentType(factory=Dummy, schema=DummySchema, title="Dummy")
        self.config.add_content(DummyContent)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api import RestAPI
        return RestAPI

    def test_create(self):
        root = self.config.registry.content('Root')
        request = testing.DummyRequest(method='POST', GET={'type_name': 'Dummy'}, POST={'title': 'Hello'})
        apply_request_extensions(request)
        inst = self._cut(root, request)
        response = inst.create()
        self.assertIsInstance(response, Dummy)
        self.assertEqual(request.response.status, "201 Created")
        self.assertIn(response, root.values())

    def test_create_bad_type(self):
        root = self.config.registry.content('Root')
        request = testing.DummyRequest(method='POST', GET={'type_name': 'Nooo'})
        inst = self._cut(root, request)
        self.assertRaises(HTTPNotFound, inst.create)

    def test_read_root(self):
        from kedja.resources.root import Root
        root = self.config.registry.content('Root')
        request = testing.DummyRequest(method='GET')
        inst = self._cut(root, request)
        response = inst.read()
        self.assertIsInstance(response, Root)
        self.assertEqual(request.response.status, "200 OK")

    def test_read_other(self):
        root = self.config.registry.content('Root')

        dummy = Dummy(rid=2)
        root['hello'] = dummy

        request = testing.DummyRequest(method='GET')
        inst = self._cut(dummy, request)
        response = inst.read()

        self.assertIsInstance(response, Dummy)
        self.assertEqual(request.response.status, "200 OK")
        self.assertIn(response, root.values())

    def test_update(self):
        root = self.config.registry.content('Root')
        dummy = Dummy(rid=2)
        root['hello'] = dummy

        request = testing.DummyRequest(method='PUT', params={'title': 'Hello world'})
        apply_request_extensions(request)

        inst = self._cut(dummy, request)
        response = inst.update()

        self.assertEqual(response, {'changed': ['title']})
        self.assertEqual(request.response.status, "202 Accepted")
        self.assertEqual(dummy.title, "Hello world")

    def test_delete(self):
        root = self.config.registry.content('Root')
        dummy = Dummy(rid=2)
        root['hello'] = dummy

        request = testing.DummyRequest(method='DELETE')

        inst = self._cut(dummy, request)
        response = inst.delete()

        self.assertEqual(response, {'deleted': 2})
        self.assertEqual(request.response.status, "202 Accepted")
        self.assertNotIn(dummy, root.values())

    def test_list(self):
        root = self.config.registry.content('Root')
        dummy2 = Dummy(rid=2)
        root['hello'] = dummy2
        dummy3 = Dummy(rid=3)
        root['bye'] = dummy3

        request = testing.DummyRequest()

        inst = self._cut(root, request)
        response = inst.list()

        # Note: No ordering yet
        self.assertIn(dummy2, response)
        self.assertIn(dummy3, response)
        self.assertEqual(len(response), 2)
        self.assertEqual(request.response.status, "200 OK")

    def test_recursive_read(self):
        root = self.config.registry.content('Root')
        dummy2 = Dummy(rid=2)
        root['hello'] = dummy2
        dummy3 = Dummy(rid=3)
        root['bye'] = dummy3

        #Contained in 'hello'/dummy2
        dummy5 = Dummy(rid=5)
        dummy2['5'] = dummy5

        dummy6 = Dummy(rid=6)
        dummy2['6'] = dummy6

        request = testing.DummyRequest()
        apply_request_extensions(request)

        inst = self._cut(dummy2, request)
        response = inst.recursive_read()

        # Note: No ordering yet
        results = \
        {'type_name': 'Dummy', 'rid': 2, 'data': {},
         'contained': [{'type_name': 'Dummy', 'rid': 5, 'data': {}, 'contained': []},
                       {'type_name': 'Dummy', 'rid': 6, 'data': {}, 'contained': []}]}
        self.assertEqual(request.response.status, "200 OK")
        self.assertEqual(len(response['contained']), 2)
        self.assertEqual(response['contained'][0]['type_name'], 'Dummy')


class APIViewUnitTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.content')
        self.config.include('arche.mutator')
        self.config.include('kedja.resources.root')
        self.config.include('kedja.resources.wall')
        DummyContent = ContentType(factory=Dummy, schema=DummySchema, title="Dummy")
        self.config.add_content(DummyContent)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.views.api import RelationsRestAPI
        return RelationsRestAPI

    def _fixture(self):
        root = self.config.registry.content('Root')
        root['wall'] = wall = self.config.registry.content('Wall', title='Walled', rid=2)
        return wall

    def test_create_relation(self):
        wall = self._fixture()
        dummya = Dummy(rid=10)
        wall['dummya'] = dummya
        dummyb = Dummy(rid=20)
        wall['dummyb'] = dummyb

        request = testing.DummyRequest(post = MultiDict((('members', 10), ('members', 20))))
        apply_request_extensions(request)

        inst = self._cut(wall, request)
        response = inst.create_relation()

        self.assertIn('relation_id', response)
        self.assertEqual(set(wall.relations_map[response['relation_id']]), {10, 20})
        self.assertEqual(request.response.status, "201 Created")

    def test_read_relation(self):
        wall = self._fixture()
        wall.relations_map[1] = (2, 3, 4)

        request = testing.DummyRequest()
        request.subpath = ('1',)
        apply_request_extensions(request)

        inst = self._cut(wall, request)
        response = inst.read_relation()

        self.assertEqual(request.response.status, "200 OK")
        self.assertEqual(response, {'relation_id': 1, 'members': [2, 3, 4]})

    def test_update_relation(self):
        wall = self._fixture()
        wall.relations_map[1] = (4, 5, 6)
        wall['a'] = Dummy(rid=4)
        wall['b'] = Dummy(rid=5)
        wall['c'] = Dummy(rid=6)

        request = testing.DummyRequest(post = MultiDict((('members', "4"), ('members', "5"))))
        request.subpath = ('1',)
        apply_request_extensions(request)

        inst = self._cut(wall, request)
        response = inst.update_relation()

        self.assertEqual(request.response.status, "202 Accepted")
        self.assertEqual(response, {'relation_id': 1, 'members': [4, 5]})

    def test_delete_relation(self):
        wall = self._fixture()
        wall.relations_map[1] = (2, 3, 4)

        request = testing.DummyRequest()
        request.subpath = ('1',)
        apply_request_extensions(request)

        inst = self._cut(wall, request)
        response = inst.delete_relation()

        self.assertEqual(request.response.status, "202 Accepted")
        self.assertEqual(response, {'deleted': 1})

    def test_list_contained_relations(self):
        wall = self._fixture()
        wall['collection1'] = collection1 = Dummy(rid=3)
        wall['collection2'] = collection2 = Dummy(rid=4)
        collection1['card1'] = Dummy(rid=11)
        collection2['card2'] = Dummy(rid=12)
        collection2['card3'] = Dummy(rid=13)

        wall.relations_map[1] = (11, 12)
        wall.relations_map[2] = (11, 13)
        wall.relations_map[3] = (11, 12, 13)

        request = testing.DummyRequest()
        #request.subpath = ('2',)
        apply_request_extensions(request)

        inst = self._cut(wall, request)
        response = inst.list_contained_relations()

        self.assertEqual(request.response.status, "200 OK")
        self.assertIn({'relation_id': 1, 'members': [11, 12]}, response)
        self.assertEqual(len(response), 3)  # 3 relations


# class APIViewUnitTests(TestCase):
#
#     def setUp(self):
#         self.config = testing.setUp()
#         self.config.include('arche.content')
#         self.config.include('arche.mutator')
#         self.config.include('kedja.resources.root')
#         DummyContent = ContentType(factory=Dummy, schema=DummySchema, title="Dummy")
#         self.config.add_content(DummyContent)
#
#     def tearDown(self):
#         testing.tearDown()
#
#     @property
#     def _cut(self):
#         from kedja.views.api import APIView
#         return APIView
#
#     def test_create(self):
#         root = self.config.registry.content('Root')
#         request = testing.DummyRequest(method='POST', params={'title': 'Hello'})
#         request.matchdict['type_name'] = 'Dummy'
#         request.matchdict['parent_rid'] = 1  # Root
#         apply_request_extensions(request)
#         inst = self._cut(root, request)
#         response = inst.create()
#         self.assertIsInstance(response, Dummy)
#         self.assertEqual(request.response.status, "201 Created")
#         self.assertIn(response, root.values())
#
#     def test_create_bad_type(self):
#         root = self.config.registry.content('Root')
#         request = testing.DummyRequest(method='POST')
#         request.matchdict['type_name'] = 'Nooo'
#         request.matchdict['parent_rid'] = 1  # Root
#         inst = self._cut(root, request)
#         self.assertRaises(HTTPNotFound, inst.create)
#
#     def test_read_root(self):
#         from kedja.resources.root import Root
#         root = self.config.registry.content('Root')
#         request = testing.DummyRequest(method='GET')
#         request.matchdict['type_name'] = 'Root'
#         request.matchdict['rid'] = "1"  # Root
#         inst = self._cut(root, request)
#         response = inst.read()
#         self.assertIsInstance(response, Root)
#         self.assertEqual(request.response.status, "200 OK")
#
#     def test_read_other(self):
#         root = self.config.registry.content('Root')
#
#         dummy = Dummy()
#         dummy.rid = 2
#         root['hello'] = dummy
#
#         request = testing.DummyRequest(method='GET')
#         request.matchdict['type_name'] = 'Dummy'
#         request.matchdict['rid'] = "2"
#
#         inst = self._cut(root, request)
#         response = inst.read()
#
#         self.assertIsInstance(response, Dummy)
#         self.assertEqual(request.response.status, "200 OK")
#         self.assertIn(response, root.values())
#
#     def test_read_wrong_type(self):
#         root = self.config.registry.content('Root')
#         request = testing.DummyRequest(method='GET')
#         request.matchdict['type_name'] = 'Woot'
#         request.matchdict['rid'] = "1"  # Root
#         inst = self._cut(root, request)
#         self.assertRaises(HTTPNotFound, inst.read)
#
#     def test_update(self):
#         root = self.config.registry.content('Root')
#         dummy = Dummy()
#         dummy.rid = 2
#         root['hello'] = dummy
#
#         request = testing.DummyRequest(method='PUT', params={'title': 'Hello world'})
#         request.matchdict['type_name'] = 'Dummy'
#         request.matchdict['rid'] = 2
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.update()
#
#         self.assertEqual(response, {'changed': ['title']})
#         self.assertEqual(request.response.status, "202 Accepted")
#         self.assertEqual(dummy.title, "Hello world")
#
#     def test_delete(self):
#         root = self.config.registry.content('Root')
#         dummy = Dummy()
#         dummy.rid = 2
#         root['hello'] = dummy
#
#         request = testing.DummyRequest(method='DELETE')
#         request.matchdict['type_name'] = 'Dummy'
#         request.matchdict['rid'] = "2"
#
#         inst = self._cut(root, request)
#         response = inst.delete()
#
#         self.assertEqual(response, {'deleted': 2})
#         self.assertEqual(request.response.status, "202 Accepted")
#         self.assertNotIn(dummy, root.values())
#
#     def test_list(self):
#         root = self.config.registry.content('Root')
#         dummy2 = Dummy()
#         dummy2.rid = 2
#         root['hello'] = dummy2
#         dummy3 = Dummy()
#         dummy3.rid = 3
#         root['bye'] = dummy3
#
#         request = testing.DummyRequest()
#         request.matchdict['type_name'] = 'Dummy'
#         request.matchdict['parent_rid'] = "1"
#
#         inst = self._cut(root, request)
#         response = inst.list()
#
#         # Note: No ordering yet
#         self.assertIn(dummy2, response)
#         self.assertIn(dummy3, response)
#         self.assertEqual(len(response), 2)
#         self.assertEqual(request.response.status, "200 OK")
#
#     def test_recursive_read(self):
#         root = self.config.registry.content('Root')
#         dummy2 = Dummy()
#         dummy2.rid = 2
#         root['hello'] = dummy2
#         dummy3 = Dummy()
#         dummy3.rid = 3
#         root['bye'] = dummy3
#
#         #Contained in 'hello'/dummy2
#         dummy5 = Dummy()
#         dummy5.rid = 5
#         dummy2['5'] = dummy5
#
#         dummy6 = Dummy()
#         dummy6.rid = 6
#         dummy2['6'] = dummy6
#
#         request = testing.DummyRequest()
#         request.matchdict['rid'] = "2"
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.recursive_read()
#
#         # Note: No ordering yet
#         results = \
#         {'type_name': 'Dummy', 'rid': 2, 'data': {},
#          'contained': [{'type_name': 'Dummy', 'rid': 5, 'data': {}, 'contained': []},
#                        {'type_name': 'Dummy', 'rid': 6, 'data': {}, 'contained': []}]}
#         self.assertEqual(request.response.status, "200 OK")
#         self.assertEqual(len(response['contained']), 2)
#         self.assertEqual(response['contained'][0]['type_name'], 'Dummy')
#
#     def test_create_relation(self):
#         root = self.config.registry.content('Root')
#         dummy2 = Dummy(rid=2)
#         root['hello'] = dummy2
#         dummy3 = Dummy(rid=3)
#         root['bye'] = dummy3
#
#         request = testing.DummyRequest()
#         request.matchdict['rids'] = ("2", "3")
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.create_relation()
#
#         self.assertIn('relation_id', response)
#         self.assertEqual(set(root.relations_map[response['relation_id']]), {2, 3})
#         self.assertEqual(request.response.status, "201 Created")
#
#     def test_read_relation(self):
#         root = self.config.registry.content('Root')
#         root.relations_map[1] = (2, 3, 4)
#
#         request = testing.DummyRequest()
#         request.matchdict['relation_id'] = "1"
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.read_relation()
#
#         self.assertEqual(request.response.status, "200 OK")
#         self.assertEqual(response, {'relation_id': 1, 'members': [2, 3, 4]})
#
#     def test_update_relation(self):
#         root = self.config.registry.content('Root')
#         root.relations_map[1] = (2, 3, 4)
#
#         request = testing.DummyRequest()
#         request.matchdict['relation_id'] = "1"
#         request.matchdict['rids'] = ("2", "3")
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.update_relation()
#
#         self.assertEqual(request.response.status, "202 Accepted")
#         self.assertEqual(response, {'relation_id': 1, 'members': [2, 3]})
#
#     def test_delete_relation(self):
#         root = self.config.registry.content('Root')
#         root.relations_map[1] = (2, 3, 4)
#
#         request = testing.DummyRequest()
#         request.matchdict['relation_id'] = "1"
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.delete_relation()
#
#         self.assertEqual(request.response.status, "202 Accepted")
#         self.assertEqual(response, {'deleted': 1})
#
#     def test_list_contained_relations(self):
#         root = self.config.registry.content('Root')
#
#         root['wall'] = wall = Dummy(rid=2)
#         wall['collection1'] = collection1 = Dummy(rid=3)
#         wall['collection2'] = collection2 = Dummy(rid=4)
#         collection1['card1'] = Dummy(rid=11)
#         collection2['card2'] = Dummy(rid=12)
#         collection2['card3'] = Dummy(rid=13)
#
#         root.relations_map[1] = (11, 12)
#         root.relations_map[2] = (11, 13)
#         root.relations_map[3] = (11, 12, 13)
#
#         request = testing.DummyRequest()
#         request.matchdict['rid'] = "2"
#         apply_request_extensions(request)
#
#         inst = self._cut(root, request)
#         response = inst.list_contained_relations()
#
#         self.assertEqual(request.response.status, "200 OK")
#         self.assertIn({'relation_id': 1, 'members': [11, 12]}, response)
#         self.assertEqual(len(r

# class APIViewFunctionalTests(TestCase):
#
#     def setUp(self):
#         from kedja import main
#         app = main({})
#         from webtest import TestApp
#         self.testapp = TestApp(app)
#
#     def test_home(self):
#         res = self.testapp.get('/howdy/Jane/Doe', status=200)
#         self.assertIn(b'Jane', res.body)
#         self.assertIn(b'Doe', res.body)


