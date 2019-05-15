import peppercorn
from arche.content import VIEW
from arche.content import EDIT
from arche.content import ADD
from arche.content import DELETE
from arche.interfaces import IResource
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPNotFound
from pyramid.traversal import find_root
from pyramid.view import view_config
from pyramid.view import view_defaults

from kedja.views.base import BaseView
from kedja.interfaces import IWall


def recursive_list(resource, request):
    result = resource.__json__(request)
    result['contained'] = []
    for x in resource.values():
        result['contained'].append(recursive_list(x, request))
    return result


class HelperMixin(object):

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


@view_defaults(context=IResource, renderer='json')
class RestAPI(BaseView, HelperMixin):

    @view_config(request_method='POST', permission_type=ADD)
    def create(self):
        """ Create a resource

            Use the context where you which to create the resource, for instance:
                /
                /{wall}

            GET-params:
                type_name: (string)
                    Name of the resource

            POST-params:
                Anything from the content types schema. In case this is missing,
                bad request will be raised with information about what went wrong.

            Example to create a card within a collection named 'col' for a wall called 'wall':

                /wall/col?type_name=Card

            returns the created resource
        """
        content = self.request.registry.content
        type_name = self.request.GET.get('type_name', None)
        if type_name not in content:
            raise HTTPBadRequest("No such type: %s" % type_name)
        new_res = content(type_name)
        new_res.rid = self.root.rid_map.new_rid()
        self.context.add(str(new_res.rid), new_res)
        controls = list(self.request.POST.items())
        print ("api_create params: ", controls)
        appstruct = peppercorn.parse(controls)
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            mutator.update(appstruct)
        self.request.response.status = 201  # Created
        return new_res

    @view_config(request_method='GET', permission_type=VIEW)
    def read(self):
        """ Get the current context as JSON.

            Uses exact path, for instance:
                /
                /{wall}
                /{wall}/{collection}
                /{wall}/{collection}/{card}
        """
        return self.context

    @view_config(request_method='PUT', permission_type=EDIT)
    def update(self):
        """ Update the current resource.
            Follows the contexts schema definition. Will raise BadRequest for validation errors.

            See kedja.resources for each schema

            Returns a dict with the key changed and a list with any attributes that were updated.

            Use the path of the object, for instance:

                /{wall}/{collection}

        """
        controls = self.request.params.items()
        appstruct = peppercorn.parse(controls)
        # Note: The mutator API will probably change!
        with self.request.get_mutator(self.context) as mutator:
            changed = mutator.update(appstruct)
        self.request.response.status = 202  # Accepted
        return {'changed': list(changed)}

    @view_config(request_method='DELETE', permission_type=DELETE)
    def delete(self):
        """ Delete the current context.

            Returns a dict with deleted as key and the RID of the deleted resource.
        """
        delete_rid = self.context.rid
        parent = self.context.__parent__
        del parent[self.context.__name__]
        self.request.response.status = 202  # Accepted
        return {'deleted': delete_rid}

    @view_config(name='list', request_method='GET', permission_type=VIEW)
    def list(self):
        """ Fetch all contained resources. Returns a list with each resource.

            get this view as /{somecontext}/list
            For instance:

                /list
                /{wall}/list
                /{wall}/(collectio}/list

        """
        # FIXME: correct permission check ?
        return list(self.context.values())

    @view_config(name='wall', context=IWall, request_method='GET', permission_type=VIEW)
    def recursive_read(self):
        """ Get all resources contained in a wall.

            Like: /{wall}/wall

            Returns a nested structure with all contained resources. Resources themselves  will have the key
            'contains' that will contain a list of their contained resources.
        """
        # FIXME: Only return resources the current user have access to ?
        return recursive_list(self.context, self.request)

    @view_config(request_method='OPTIONS')
    def preflight_check(self):
        """ Simply return 200 ok for OPTIONS-requests. """
        return {}


@view_defaults(context=IWall, name='relation', renderer='json')
class RelationsRestAPI(BaseView, HelperMixin):

    def get_relation_id_from_subpath(self):
        try:
            return int(self.request.subpath[0])
        except IndexError:
            raise HTTPBadRequest("No relation_id specified")
        except ValueError:
            raise HTTPBadRequest("relation_id is not an integer")

    def get_relation(self, relation_id):
        assert isinstance(relation_id, int)
        try:
            return self.context.relations_map[relation_id]
        except KeyError:
            raise HTTPNotFound("No such relation")

    @view_config(request_method='POST')
    def create_relation(self):
        """
            Create a new erlation within a wall.

                /{wall}/rerlation

            POST-pararms:
                members: sequence of RIDs, at least 2 of them. Like members=(1,2,3)

            returns the newly created relation as:
            {'relation_id': <relation_id>}

        """
        rids = []
        members = self.request.POST.getall('members')
        print (members)
        if len(members) < 2:
            raise HTTPBadRequest("'members' must have 2 or more RIDs")
        for x in members:
            # Just to make sure
            resource = self.get_resource(x)
            if resource is None:
                raise HTTPBadRequest("No resource found with rid %s" % x)
            rids.append(resource.rid)
        self.request.response.status = 201  # Created
        try:
            return {'relation_id': self.context.relations_map.create(rids)}
        except ValueError:
            raise HTTPBadRequest("Refusing to create relation since it already seem to exist. Members: %s" % ", ".join([str(x) for x in rids]))

    @view_config(request_method='GET')
    def read_relation(self):
        """ Read relation with a specific id.

            /{wall}/relation/{relation_id}

            Returns:
                {'relation_id': <relation_id>, 'members': [<rid>, <rid>, <...>]}

        """
        relation_id = self.get_relation_id_from_subpath()
        relation = self.get_relation(relation_id)
        return {'relation_id': relation_id, 'members': list(relation)}

    @view_config(request_method='PUT')
    def update_relation(self):
        """ Update relation.

            /{wall}/relation/{relation_id}

            POST-params:
                members: sequence of RIDs, at least 2 of them. Like members=(1,2,3)

            returns same as read
        """
        relation_id = self.get_relation_id_from_subpath()
        self.get_relation(relation_id)  # To check existance, will raise 404
        rids = []
        members = self.request.POST.getall('members')
        if len(members) < 2:
            raise HTTPBadRequest("'members' must have 2 or more RIDs")
        for x in members:
            # Just to make sure
            resource = self.get_resource(x)
            if resource is None:
                raise HTTPBadRequest("No resource found with rid %s" % x)
            rids.append(resource.rid)
        try:
            self.context.relations_map[relation_id] = rids
        except ValueError as exc:
            raise HTTPBadRequest(exc)
        self.request.response.status = 202  # Accepted
        return {'relation_id': int(relation_id), 'members': list(rids)}

    @view_config(request_method='DELETE')
    def delete_relation(self):
        """ Delete relation

            /{wall}/relation/{relation_id}
        """
        relation_id = self.get_relation_id_from_subpath()
        try:
            del self.context.relations_map[relation_id]
        except KeyError:
            raise HTTPNotFound("No such relation")
        self.request.response.status = 202  # Accepted
        return {'deleted': relation_id}

    @view_config(name='list_relations', request_method='GET')
    def list_contained_relations(self):
        """ List all contained relations within this wall.

            /{wall}/list_relations

            Returns a list of all relations in the same structure as the read function.
        """
        contained_rids = self.root.rid_map.contained_rids(self.context)
        results = []
        for relation_id in self.context.relations_map.find_relevant_relation_ids([self.context.rid] + list(contained_rids)):
            results.append(
                {'relation_id': relation_id, 'members': list(self.context.relations_map[relation_id])}
            )
        return results

    @view_config(request_method='OPTIONS')
    def preflight_options_requests(self):
        """ Simply return 200 ok for OPTIONS-requests. """
        # FIXME: Send a debug message?
        return {}


def includeme(config):
    config.scan(__name__)
