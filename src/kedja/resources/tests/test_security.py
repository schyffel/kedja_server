from unittest import TestCase

from arche.authentication.models import StaticAuthenticationPolicy
from arche.content import ContentType
from kedja.interfaces import ISecurityAware
from kedja.testing import get_settings, TestingAuthenticationPolicy
from pyramid import testing
from pyramid.request import apply_request_extensions


from pyramid.security import ALL_PERMISSIONS, remember, Everyone, Deny, Allow, DENY_ALL
from zope.interface.verify import verifyObject


class SecurityAwareMixinTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _resource(self):
        from arche.folder import Folder
        from kedja.resources.security import SecurityAwareMixin

        class DummySecurityAware(Folder, SecurityAwareMixin):
            acl_name = ""

        return DummySecurityAware

    @property
    def _named_acl(self):
        from kedja.models.acl import NamedACL
        return NamedACL

    def _fixture(self):
        self.config.include('kedja.config')

        # ACL fixture
        parent_acl = self._named_acl('parent')
        parent_acl.add_allow('Admin', ['edit', 'comment', 'delete'])
        parent_acl.add_allow('User', 'comment')
        parent_acl.add_allow(Everyone, 'view')

        child_acl = self._named_acl('child')
        child_acl.add_allow('Owner', ['edit', 'delete'])
        self.config.add_acl(parent_acl)
        self.config.add_acl(child_acl)

        # Fixture
        parent = self._resource(acl_name='parent')
        child = self._resource(acl_name='child')
        parent['c'] = child
        parent.add_user_roles(1, 'Admin')
        parent.add_user_roles(2, 'User')
        child.add_user_roles(3, 'Owner')
        return parent

    def test_interface(self):
        resource = self._resource()
        self.failUnless(verifyObject(ISecurityAware, resource))

    def test_add_user_roles(self):
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        obj.add_user_roles(1, 'a', 'b', 'c')
        self.assertEqual({'a', 'b', 'c'}, obj.get_roles(1))
        obj.add_user_roles('1', 'c', 'd')
        self.assertEqual({'a', 'b', 'c', 'd'}, obj.get_roles(1))

    def test_remove_user_roles(self):
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        obj.add_user_roles(1, 'a', 'b', 'c')
        self.assertEqual({'a', 'b', 'c'}, obj.get_roles(1))
        obj.remove_user_roles(1, 'c', 'd')
        self.assertEqual({'a', 'b'}, obj.get_roles(1))
        obj.remove_user_roles('1', 'b', 'd')
        self.assertEqual({'a'}, obj.get_roles(1))

    def test_remove_user_roles_dont_die_on_key_error(self):
        obj = self._resource()
        self.assertEqual(set(), obj.get_roles(1))
        obj.remove_user_roles(1, 'c', 'd')

    def test_get_computed_acl(self):
        self.config.include('kedja.config')
        named_acl = self._named_acl('test_acl')
        named_acl.add_allow('role', ['perm-one', 'perm-two'])
        self.config.add_acl(named_acl)
        obj = self._resource(acl_name='test_acl')
        request = testing.DummyRequest()
        obj.add_user_roles(1, 'role')
        self.assertEqual([(Deny, Everyone, ALL_PERMISSIONS)], list(obj.get_computed_acl(['2'], request)))
        self.assertEqual(
            [(Allow, '1', ('perm-one', 'perm-two')), (Deny, Everyone, ALL_PERMISSIONS)],
            list(obj.get_computed_acl(['1'], request))
        )

    def test_get_computed_acl_several(self):
        parent = self._fixture()
        request = testing.DummyRequest()
        self.assertEqual(
            list(parent.get_computed_acl([1, 2, 3], request)),
            [
                (Allow, '1', ('edit', 'comment', 'delete')),
                (Allow, '2', ('comment',)),
                (Allow, Everyone, ('view',)),
                (Deny, Everyone, ALL_PERMISSIONS),
            ]
        )

    def test_get_computed_acl_broken_acl(self):
        parent = self._fixture()
        child = parent['c']
        child.acl_name = '404'
        request = testing.DummyRequest()
        # Simply the parents ACL
        self.assertEqual(
            list(child.get_computed_acl([1, 2, 3], request)),
            [
                (Allow, '1', ('edit', 'comment', 'delete')),
                (Allow, '2', ('comment',)),
                (Allow, Everyone, ('view',)),
                (Deny, Everyone, ALL_PERMISSIONS),
            ]
        )

    def test_get_roles_map(self):
        parent = self._fixture()
        self.assertEqual({'1': {'Admin'}, '2': {'User'}}, parent.get_roles_map([1, 2, 3]))
        child = parent['c']
        self.assertEqual({'3': {'Owner'}}, child.get_roles_map([1, 2, 3]))

    def test_get_acl(self):
        parent = self._fixture()
        acl = parent.get_acl()
        self.assertEqual(
            [
                ('Allow', 'Admin', ('edit', 'comment', 'delete')),
                ('Allow', 'User', ('comment',)),
                ('Allow', 'system.Everyone', ('view',))
            ],
            acl
        )

    def test_get_acl_nothing_registered(self):
        parent = self._fixture()
        parent.acl_name = ''
        self.assertEqual(None, parent.get_acl())

    def test_acl_method(self):
        self.config.testing_securitypolicy(userid='2')
        request = testing.DummyRequest()
        self.config.begin(request)
        parent = self._fixture()
        self.assertEqual(
            [
                (Allow, '2', ('comment',)),
                (Allow, 'system.Everyone', ('view',)),
                DENY_ALL
            ],
            list(parent.__acl__())
        )

    def test_integration(self):
        parent = self._fixture()
        self.config.include('kedja.testing')
        self.config.set_authentication_policy(StaticAuthenticationPolicy())
        request = testing.DummyRequest()
        self.config.begin(request)
        remember(request, '2')
        self.assertTrue(request.has_permission('comment', parent))
        self.assertTrue(request.has_permission('view', parent))
        self.assertFalse(request.has_permission('edit', parent))


class SetRoleFromAuthenticatedTests(TestCase):

    def setUp(self):
        self.config = testing.setUp(settings=get_settings())
        self.config.include('kedja.testing')

    def tearDown(self):
        testing.tearDown()

    @property
    def _resource(self):
        from arche.folder import Folder
        from kedja.resources.security import SecurityAwareMixin

        class DummySecurityAware(Folder, SecurityAwareMixin):
            type_name = 'Dummy'
            acl_name = ""

        return DummySecurityAware

    def test_set_role_from_authenticated(self):
        ct = ContentType(self._resource, ownership_role='SomeRole')
        self.config.add_content(ct)
        self.config.set_authentication_policy(TestingAuthenticationPolicy(userid='10'))
        request = testing.DummyRequest()
        self.config.begin(request)
        content = self.config.registry.content
        root = content('Root')
        root['dummy'] = dummy = content('Dummy')
        self.assertEqual({'SomeRole'}, dummy.get_roles(10))
