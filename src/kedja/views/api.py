import peppercorn
from arche.content import VIEW
from arche.content import EDIT
from arche.content import ADD
from arche.content import DELETE
from colander_jsonschema import convert
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import find_root
from pyramid.view import view_config
from pyramid.view import view_defaults

from kedja.views.base import BaseView


@view_defaults(renderer='json')
class APIView(BaseView):

    def get_resource(self, rid):
        try:
            rid = int(rid)
        except ValueError:  # pragma: no coverage
            return
        return self.root.rid_map.get_resource_or_404(rid)

    @property
    def content(self):
        return self.request.registry.content

    @reify
    def root(self):
        return find_root(self.context)

    def _check_type_name(self, resource):
        if self.content.get_type(resource) != self.request.matchdict['type_name']:
            raise HTTPNotFound("Not that type of resource")

    @view_config(route_name='api_create', request_method='POST')
    def create(self):
        """ Create a content type at 'rid'.
        """
        type_name = self.request.matchdict['type_name']
        if type_name not in self.content:
            raise HTTPNotFound("No such type: %s" % type_name)
        parent = self.get_resource(self.request.matchdict['parent_rid'])
        access = self.content.has_permission_type(parent, self.request, ADD, type_name=type_name)
        if not access:
            raise HTTPForbidden("You lack the permission to create this resource at %s" % parent, result=access)
        new_res = self.content(type_name)
        new_res.rid = self.root.rid_map.new_rid()
        parent.add(str(new_res.rid), new_res)
        self.request.response.status = 201  # Created
        return new_res

    @view_config(route_name='api_read', request_method='GET')
    def read(self):
        resource = self.get_resource(self.request.matchdict['rid'])
        self._check_type_name(resource)
        access = self.content.has_permission_type(resource, self.request, VIEW)
        if not access:
            raise HTTPForbidden("You lack the permission to read this resource", result=access)
        return resource

    @view_config(route_name='api_update', request_method='PUT')
    def update(self):
        resource = self.get_resource(self.request.matchdict['rid'])
        self._check_type_name(resource)
        access = self.content.has_permission_type(resource, self.request, EDIT)
        if not access:
            raise HTTPForbidden("You lack the permission to update this resource", result=access)
        controls = self.request.params.items()
        appstruct = peppercorn.parse(controls)
        # Note: The mutator API will probably change!
        with self.request.get_mutator(resource) as mutator:
            changed = mutator.update(appstruct)
        self.request.response.status = 202  # Accepted
        return {'changed': list(changed)}

    @view_config(route_name='api_delete', request_method='DELETE')
    def delete(self):
        resource = self.get_resource(self.request.matchdict['rid'])
        self._check_type_name(resource)
        access = self.content.has_permission_type(resource, self.request, DELETE)
        if not access:
            raise HTTPForbidden("You lack the permission to delete this resource", result=access)
        parent = resource.__parent__
        del parent[resource.__name__]
        self.request.response.status = 202  # Accepted
        return {'deleted': int(self.request.matchdict['rid'])}

    @view_config(route_name='api_list', request_method='GET')
    def list(self):
        # FIXME: Only return resources the current user have access to
        resource = self.get_resource(self.request.matchdict['parent_rid'])
        requested_type_name = self.request.matchdict['type_name']
        results = []
        for x in resource.values():
            if self.content.get_type(x) == requested_type_name:
                results.append(x)
        return results

    @view_config(route_name='api_update_schema', request_method='GET')
    def schema_update(self):
        rid = self.request.matchdict['rid']
        rid = int(rid) # Validate
        context = self.root.rid_map.get_resource_or_404(rid)
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
    # List contents
    config.add_route('api_list', '/api/list/{type_name}/{parent_rid}')
    # Schema-definitions - Update
    config.add_route('api_update_schema', '/api/schema/update/{rid}')
    # Create relation
    # FIXME
    # Update relation

    # Remove relation

    config.scan(__name__)
