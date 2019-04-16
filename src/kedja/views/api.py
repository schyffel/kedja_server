import peppercorn
from arche.content import VIEW
from arche.content import EDIT
from arche.content import ADD
from arche.content import DELETE
from colander_jsonschema import convert
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden, HTTPBadRequest
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

    @view_config(route_name='api_recursive_read', request_method='GET')
    def recursive_read(self):
        # FIXME: Only return resources the current user have access to
        resource = self.get_resource(self.request.matchdict['rid'])
        return self.recursive_list(resource)

    def recursive_list(self, resource):
        result = resource.__json__(self.request)
        result['contained'] = []
        for x in resource.values():
            result['contained'].append(self.recursive_list(x))
        return result

    @view_config(route_name='api_update_schema', request_method='GET')
    def schema_update(self):
        rid = self.request.matchdict['rid']
        rid = int(rid) # Validate
        context = self.root.rid_map.get_resource_or_404(rid)
        schema = self.request.registry.content.get_schema(context, request=self.request)
        converted = convert(schema)
        return converted

    @view_config(route_name='api_create_relation', request_method='POST')
    def create_relation(self):
        rids = []
        for x in self.request.matchdict['rids']:
            # Just to make sure
            resource = self.get_resource(x)
            rids.append(resource.rid)
        self.request.response.status = 201  # Created

        try:
            return {'relation_id': self.root.relations_map.create(rids)}
        except ValueError:
            raise HTTPBadRequest("Refusing to create relation since it already seem to exist. Members: %s" % ", ".join(rids))

    def get_relation(self, relation_id):
        relation_id = relation_id
        try:
            relation_id = int(relation_id)
        except ValueError:
            raise HTTPBadRequest("Supplied relation_id is not an integer")
        try:
            return self.root.relations_map[relation_id]
        except KeyError:
            raise HTTPNotFound("No such relation")

    @view_config(route_name='api_read_relation', request_method='GET')
    def read_relation(self):
        relation_id = self.request.matchdict['relation_id']
        # Validate, check int possible etc
        relation = self.get_relation(relation_id)
        return {'relation_id': int(relation_id), 'members': list(relation)}

    @view_config(route_name='api_update_relation', request_method='PUT')
    def update_relation(self):
        try:
            relation_id = int(self.request.matchdict['relation_id'])
        except ValueError:
            raise HTTPBadRequest("Supplied relation_id is not an integer")
        try:
            rids = [int(x) for x in self.request.matchdict['rids']]
        except ValueError as exc:
            raise HTTPBadRequest(exc)
        try:
            self.root.relations_map[relation_id] = rids
        except ValueError as exc:
            raise HTTPBadRequest(exc)
        self.request.response.status = 202  # Accepted
        return {'relation_id': int(relation_id), 'members': list(rids)}

    @view_config(route_name='api_delete_relation', request_method='DELETE')
    def delete_relation(self):
        try:
            relation_id = int(self.request.matchdict['relation_id'])
        except ValueError:
            raise HTTPBadRequest("Supplied relation_id is not an integer")
        try:
            del self.root.relations_map[relation_id]
        except KeyError:
            raise HTTPNotFound("No such relation")
        self.request.response.status = 202  # Accepted
        return {'deleted': relation_id}

    @view_config(route_name='api_list_relations', request_method='GET')
    def list_contained_relations(self):
        resource = self.get_resource(self.request.matchdict['rid'])
        contained_rids = self.root.rid_map.contained_rids(resource)
        results = []
        for relation_id in self.root.relations_map.find_relevant_relation_ids([resource.rid] + list(contained_rids)):
            results.append(
                {'relation_id': relation_id, 'members': list(self.root.relations_map[relation_id])}
            )
        return results


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
    # Get all of the content contained within the resource specified at parent_rid
    config.add_route('api_recursive_read', '/api/recursive_read/{rid}')
    # Schema-definitions - Update
    config.add_route('api_update_schema', '/api/schema/update/{rid}')
    # Create relation
    config.add_route('api_create_relation', '/api/create_relation/*rids')
    # Read relation
    config.add_route('api_read_relation', '/api/read_relation/{relation_id}')
    # Update relation
    config.add_route('api_update_relation', '/api/update_relation/{relation_id}*rids')
    # Delete relation
    config.add_route('api_delete_relation', '/api/delete_relation/{relation_id}')
    # List all contained relations
    config.add_route('api_list_relations', '/api/list_contained_relations/{rid}')
    config.scan(__name__)
