from json import JSONDecodeError
from logging import getLogger

import colander


logger = getLogger(__name__)


class ResourceAPIBase(object):

    def __init__(self, request, context=None):
        self.request = request
        self.context = context
        self._lookup_cache = {}

    def get_resource(self, rid):
        if isinstance(rid, str):
            try:
                rid = int(rid)
            except ValueError:
                return
        return self._lookup_cache.setdefault(rid, self.request.root.rid_map.get_resource(rid))

    def error(self, request, msg="Doesn't exist", type='path', status=404):
        request.errors.add(type, msg)
        request.errors.status = status

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict.get('type_name', object())
        if type_name not in request.registry.content:
            return self.error(request, msg="'type_name' specified doesn't exist.")

    def validate_rid(self, request, **kw):
        """ RID must be numeric and exist. """
        rid = self.request.matchdict['rid']
        if self.get_resource(rid) is None:
            return self.error(request, "No resource with rid %r exists" % rid)

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict['type_name']
        if type_name not in request.registry.content:
            return self.error(request, "No resource called %s" % type_name)

    def get_json_appstruct(self):
        try:
            return self.request.json_body
        except JSONDecodeError as exc:
            logger.debug("JSON decode error during PUT", exc_info=exc)
            return self.error(self.request, "JSON decode error: %s" % exc, type='body', status=400)

    def base_get(self):
        """ Get specific resource """
        return self.get_resource(self.request.matchdict['rid'])

    def base_put(self):
        """ Update a resource """
        rid = self.request.matchdict['rid']
        resource = self.get_resource(rid)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(resource) as mutator:
            changed = mutator.update(appstruct)
        # Log changed
        return resource

    def base_delete(self):
        """ Delete a resource """
        rid = self.request.matchdict['rid']
        resource = self.get_resource(rid)
        parent = resource.__parent__
        parent.remove(resource.__name__)
        return {'removed': rid}


class ContainedAPI(ResourceAPIBase):

    @property
    def create_type(self):
        raise NotImplementedError("Must be set on subclass")

    def collection_get(self):
        return list(self.context.values())

    def collection_post(self):
        new_res = self.request.registry.content(self.create_type)
        new_res.rid = self.root.rid_map.new_rid()
        # Should be the root
        self.context.add(str(new_res.rid), new_res)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        return {'changed': list(changed)}


class RIDPathSchema(colander.Schema):
    rid = colander.SchemaNode(
        colander.Int(),
    )


class SubRIDPathSchema(RIDPathSchema):
    subrid = colander.SchemaNode(
        colander.Int(),
    )


class ResourceSchema(colander.Schema):
    path = RIDPathSchema()


class BaseResponseSchema(colander.Schema):
    rid = colander.SchemaNode(
        colander.Int(),
    )
    type_name = colander.SchemaNode(
        colander.String(),
    )
