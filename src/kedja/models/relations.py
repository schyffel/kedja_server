from random import randrange

from BTrees import family64
from BTrees.OOBTree import OOSet
from persistent import Persistent


class RelationMap(Persistent):
    family = family64

    def __init__(self):
        self.rid_to_relations = self.family.IO.BTree()
        self.relation_to_rids = self.family.IO.BTree()

    def __getitem__(self, relation_id:int):
        return self.relation_to_rids[relation_id]

    def __delitem__(self, relation_id:int):
        for x in self.get(relation_id, ()):
            linked = self.rid_to_relations.get(x, ())
            if relation_id in linked:
                linked.remove(relation_id)
                if not linked:
                    del self.rid_to_relations[x]
        del self.relation_to_rids[relation_id]

    def __setitem__(self, relation_id, rids):
        assert isinstance(relation_id, int)
        if relation_id in self:
            del self[relation_id]
        for x in rids:
            assert isinstance(x, int)
            if x not in self.rid_to_relations:
                self.rid_to_relations[x] = OOSet()
            self.rid_to_relations[x].add(relation_id)
        self.relation_to_rids[relation_id] = OOSet(rids)

    def __contains__(self, relation_id:int):
        return relation_id in self.relation_to_rids

    def get(self, relation_id, default=None):
        return self.relation_to_rids.get(relation_id, default)

    def new_relation_id(self):
        """ Get an unused ID. It's not reserved in any way, so make sure to use it within the current transaction.
            In the unlikely case that the same ID would be used, a transaction error will occur.
        """
        relation_id = None
        while not relation_id:  # We don't like 0 either
            relation_id = randrange(self.family.minint, self.family.maxint)
            if relation_id in self.relation_to_rids: # pragma: no cover
                relation_id = None
        return relation_id
