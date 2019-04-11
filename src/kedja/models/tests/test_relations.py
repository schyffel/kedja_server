from unittest import TestCase

from pyramid import testing


class RelationsTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from kedja.models.relations import RelationMap
        return RelationMap

    def test_setitem(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        self.assertIn(1, map.relation_to_rids)
        self.assertIn(2, map.relation_to_rids[1])
        self.assertEqual(set(map.relation_to_rids[1]), set([1, 2, 3]))

    def test_del_cleans_up(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        del map[1]
        self.assertFalse(len(map.relation_to_rids))
        self.assertFalse(len(map.rid_to_relations))

    def test_getitem(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        self.assertEqual(set(map[1]), set([1, 2, 3]))

    def test_reset_relation(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        map[1] = (5, 6)
        self.assertEqual(set(map.relation_to_rids[1]), set([5, 6]))

    def test_new_relation_id(self):
        map = self._cut()
        self.assertIsInstance(map.new_relation_id(), int)

    def test_find_relation(self):
        map = self._cut()
        map[1] = (1, 2, 3)
        map[2] = (2, 3)
        self.assertEqual(map.find_relations(1, 2, 3), {1})
        self.assertEqual(map.find_relations(3), {1, 2})
        self.assertEqual(map.find_relations(2, 3), {1, 2})
        self.assertEqual(map.find_relations(1, 2), {1})
