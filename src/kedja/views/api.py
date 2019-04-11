import peppercorn
from arche.content import VIEW
from arche.content import EDIT
from arche.content import ADD
from arche.content import DELETE
from colander_jsonschema import convert
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.view import view_defaults

from kedja.views.base import BaseView


@view_defaults(renderer='json')
class APIView(BaseView):

    def get_resource(self, rid):
        try:
            rid = int(rid)
        except ValueError:
            return
        return self.request.root.rid_map.get_resource_or_404(rid)

    @property
    def content(self):
        return self.request.registry.content

    @view_config(route_name='api_create')
    def create(self):
        type_name = self.request.matchdict['type_name']
        if type_name not in self.content:
            raise HTTPNotFound("No such type: %s" % type_name)
        parent = self.get_resource(self.request.matchdict['rid'])
        access = self.content.has_permission_type(parent, self.request, ADD, type_name=type_name)
        if not access:
            raise HTTPForbidden("You lack the permission to create this resource at %s" % parent, result=access)
        new_res = self.content(type_name)
        new_res.rid = self.request.root.rid_map.new_rid()
        parent.add(str(new_res.rid), new_res)
        return new_res

    @view_config(route_name='api_read')
    def read(self):
        resource = self.get_resource(self.request.matchdict['rid'])
        access = self.content.has_permission_type(resource, self.request, VIEW)
        if not access:
            raise HTTPForbidden("You lack the permission to read this resource", result=access)
        return resource

    @view_config(route_name='api_update')
    def update(self):
        context = self.get_resource(self.request.matchdict['rid'])
        access = self.content.has_permission_type(context, self.request, EDIT)
        if not access:
            raise HTTPForbidden("You lack the permission to update this resource", result=access)
        controls = self.request.POST.items()
        appstruct = peppercorn.parse(controls)
        # Note: The mutator API will probably change!
        with self.request.get_mutator(context) as mutator:
            changed = mutator.update(appstruct)
        return {'changed': list(changed)}

    @view_config(route_name='api_delete')
    def delete(self):
        context = self.get_resource(self.request.matchdict['rid'])
        access = self.content.has_permission_type(context, self.request, DELETE)
        if not access:
            raise HTTPForbidden("You lack the permission to delete this resource", result=access)
        parent = context.__parent__
        del parent[context.__name__]
        return {}

    @view_config(route_name='api_update_schema')
    def schema_update(self):
        rid = self.request.matchdict['rid']
        rid = int(rid) # Validate
        context = self.request.root.rid_map.get_resource_or_404(rid)
        schema = self.request.registry.content.get_schema(context, request=self.request)
        converted = convert(schema)
        return converted


def includeme(config):
    # Create
    config.add_route('api_create', '/api/create/{type_name}/{parent_rid}')
    # Read
    config.add_route('api_read', '/api/read/{type_name}/{rid}')
    # Update
    config.add_route('api_update', '/api/update/{type_name}/{rid}')
    # Delete
    config.add_route('api_delete', '/api/delete/{type_name}/{rid}')
    # Schema-definitions - Update
    config.add_route('api_update_schema', '/api/schema/update/{rid}')
    config.scan(__name__)
