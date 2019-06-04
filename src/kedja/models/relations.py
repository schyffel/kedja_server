from random import randrange

from BTrees import family64
from BTrees.OOBTree import OOSet
from persistent import Persistent


# FIXME: Might be smarter to have these as resources

class RelationJSON(object):

    def __init__(self, relation_id, members=()):
        self.relation_id = relation_id
        self.members = list(members)

    def __json__(self, request):
        return self.asdict()

    def __str__(self):
        return str(self.asdict())

    def __repr__(self):
        return '<Relation %r with %r>' % (self.relation_id, self.members)

    def asdict(self):
        return {'relation_id': self.relation_id, 'members': self.members}

    def __len__(self):
        return len(self.members)

    def __iter__(self):
        return iter(self.asdict().items())

    def __eq__(self, other):
        if isinstance(other, RelationJSON):
            return other.asdict() == self.asdict()
        return other == self.asdict()


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
        self.can_create_relation(rids)
        if relation_id in self:
            del self[relation_id]
        for x in rids:
            assert isinstance(x, int)
            if x not in self.rid_to_relations:
                self.rid_to_relations[x] = OOSet()
            self.rid_to_relations[x].add(relation_id)
        self.relation_to_rids[relation_id] = tuple(rids)

    def __contains__(self, relation_id:int):
        return relation_id in self.relation_to_rids

    def create(self, rids):
        relation_id = self.new_relation_id()
        self[relation_id] = rids
        return relation_id

    def can_create_relation(self, rids):
        """ Make sure a relation don't exist between these rids already"""
        if len(rids) < 2:
            raise ValueError("It takes at least 2 to tango!")
        rids = tuple(rids)
        existing = self.find_relations(rids[0], *rids[1:])
        if existing:
            cmp_set = set(rids)
            for rel_id in existing:
                if self.get(rel_id) == cmp_set:
                    raise ValueError("Already has relations: %s" % ", ".join(existing))

    def get(self, relation_id, default=None):
        return self.relation_to_rids.get(relation_id, default)

    def get_as_json(self, relation_id, default=None):
        members = self.get(relation_id, None)
        if members is not None:
            return RelationJSON(relation_id, members)
        return default

    def get_all_as_json(self):
        for k in self.keys():
            yield self.get_as_json(k)

    def new_relation_id(self):
        """ Get an unused ID. It's not reserved in any way, so make sure to use it within the current transaction.
            In the unlikely case that the same ID would be used, a transaction error will occur.
        """
        relation_id = None
        js_maxint = 2**53-1
        while not relation_id:  # We don't like 0 either
            relation_id = randrange(-js_maxint, js_maxint)
            if relation_id in self.relation_to_rids: # pragma: no cover
                relation_id = None
        return relation_id

    def find_relations(self, rid:int, *rids):
        """ Get relations that has one or more rids in them
        """
        first = set(self.rid_to_relations.get(rid, ()))
        if rids:
            return first.intersection(*[self.rid_to_relations.get(x, set()) for x in rids])
        return first

    def find_relevant_relation_ids(self, rids):
        """ Return all relation_ids that have anything to do with any of the specified rids.
        """
        if isinstance(rids, int):
            rids = [rids]
        found = set()
        for x in rids:
            found.update(self.find_relations(x))
        return found

    def keys(self):
        return self.relation_to_rids.keys()

    def __len__(self):
        return len(self.relation_to_rids)
