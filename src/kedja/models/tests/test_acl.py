from unittest import TestCase

from pyramid import testing
from pyramid.security import Allow, Deny, Everyone, Authenticated, ALL_PERMISSIONS


class NamedACLTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.acl import NamedACL
        return NamedACL

    @property
    def Role(self):
        from kedja.models.acl import Role
        return Role

    def test_add_allow(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        self.assertEqual([(Allow, manager, ('filibuster', 'inspect'))], acl)

    def test_add_deny(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_deny(manager, 'spy')
        self.assertEqual(
            [
                (Allow, manager, ('filibuster', 'inspect')),
                (Deny, manager, ('spy',))
            ],
            acl)

    def test_translate_simple(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        other = self.Role('Other')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_deny(manager, 'spy')
        mapping = {'1': [manager, other], '2': [other]}
        self.assertEqual(tuple(acl.get_translated_acl(mapping)),
                         (('Allow', '1', ('filibuster', 'inspect')), ('Deny', '1', ('spy',))))

    def test_translate_with_pyramids_roles(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        other = self.Role('Other')
        acl.add_allow(manager, ['filibuster', 'inspect'])
        acl.add_allow(Authenticated, 'view')
        acl.add_deny(manager, 'spy')
        acl.add_deny(Everyone, 'edit')
        mapping = {'1': [manager, other], '2': [other]}

        expected = (
            ('Allow', '1', ('filibuster', 'inspect')),
            ('Allow', 'system.Authenticated', ('view',)),
            ('Deny', '1', ('spy',)),
            ('Deny', 'system.Everyone', ('edit',))
        )
        self.assertEqual(tuple(acl.get_translated_acl(mapping)), expected)

    def test_translate_all_permissions(self):
        acl = self._cut('test')
        manager = self.Role('Manager')
        acl.add_allow(manager, ALL_PERMISSIONS)

        mapping = {'1': [manager]}
        self.assertEqual(list(acl.get_translated_acl(mapping)),
                         [('Allow', '1', ALL_PERMISSIONS)])
