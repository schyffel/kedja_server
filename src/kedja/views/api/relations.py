import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator
from pyramid.decorator import reify

from kedja.views.api.base import RIDPathSchema
from kedja.views.api.base import RelationAPISchema
from kedja.views.api.base import RelationIDPathSchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


class RelationSchema(colander.Schema):
    members = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(
            colander.Int(),
        ),
        validator=colander.Range(2, 1000),
    )


class CreateRelationAPISchema(colander.Schema):
    path = RIDPathSchema()
    body = RelationSchema()


class UpdateRelationAPISchema(colander.Schema):
    path = RelationIDPathSchema()
    body = RelationSchema()


@resource(collection_path='/api/1/walls/{rid}/relations',
          path='/api/1/walls/{rid}/relations/{relation_id}',
          tags=['Relations'],
          schema=RelationAPISchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class RelationsAPI(ResourceAPIBase):
    #type_name = 'Relation'
    parent_type_name = 'Wall'

    @reify
    def wall(self):
        return self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)

    def get_relation_id(self):
        return int(self.request.matchdict['relation_id'])

    def get_relation(self, relation_id):
        relation = self.wall.relations_map.get_as_json(relation_id, None)
        if not relation:
            self.error(self.request, "No relation with relation_id %r" % relation_id)
        return relation

    def get(self):
        relation_id = self.get_relation_id()
        return self.get_relation(relation_id)

    @view(schema=UpdateRelationAPISchema())
    def put(self):
        relation_id = self.get_relation_id()
        appstruct = self.get_json_appstruct()
        self.wall.relations_map[relation_id] = appstruct['members']
        return self.wall.relations_map.get_as_json(relation_id)

    def delete(self):
        relation_id = self.get_relation_id()
        # FIXME
        return self.base_delete()

    @view(schema=ResourceAPISchema())
    def collection_get(self):
        return list(self.wall.relations_map.get_all_as_json())

    @view(schema=CreateRelationAPISchema())
    def collection_post(self):
        appstruct = self.get_json_appstruct()
        # The members part
        relation_id = self.wall.relations_map.create(appstruct['members'])
        return self.wall.relations_map.get_as_json(relation_id)

    def options(self):
        # FIXME:
        return {}


def includeme(config):
    config.scan(__name__)


# @view_defaults(context=IWall, name='relation', renderer='json')
# class RelationsRestAPI(BaseView, HelperMixin):
#
#     def get_relation_id_from_subpath(self):
#         try:
#             return int(self.request.subpath[0])
#         except IndexError:
#             raise HTTPBadRequest("No relation_id specified")
#         except ValueError:
#             raise HTTPBadRequest("relation_id is not an integer")
#
#     def get_relation(self, relation_id):
#         assert isinstance(relation_id, int)
#         try:
#             return self.context.relations_map[relation_id]
#         except KeyError:
#             raise HTTPNotFound("No such relation")
#
#     @view_config(request_method='POST')
#     def create_relation(self):
#         """
#             Create a new erlation within a wall.
#
#                 /{wall}/relation
#
#             POST-pararms:
#                 members: sequence of RIDs, at least 2 of them. Like members=(1,2,3)
#
#             returns the newly created relation as:
#             {'relation_id': <relation_id>}
#
#         """
#         rids = []
#         members = self.request.POST.getall('members')
#         print (members)
#         if len(members) < 2:
#             raise HTTPBadRequest("'members' must have 2 or more RIDs")
#         for x in members:
#             # Just to make sure
#             resource = self.get_resource(x)
#             if resource is None:
#                 raise HTTPBadRequest("No resource found with rid %s" % x)
#             rids.append(resource.rid)
#         self.request.response.status = 201  # Created
#         try:
#             return {'relation_id': self.context.relations_map.create(rids)}
#         except ValueError:
#             raise HTTPBadRequest("Refusing to create relation since it already seem to exist. Members: %s" % ", ".join([str(x) for x in rids]))
#
#     @view_config(request_method='GET')
#     def read_relation(self):
#         """ Read relation with a specific id.
#
#             /{wall}/relation/{relation_id}
#
#             Returns:
#                 {'relation_id': <relation_id>, 'members': [<rid>, <rid>, <...>]}
#
#         """
#         relation_id = self.get_relation_id_from_subpath()
#         relation = self.get_relation(relation_id)
#         return {'relation_id': relation_id, 'members': list(relation)}
#
#     @view_config(request_method='PUT')
#     def update_relation(self):
#         """ Update relation.
#
#             /{wall}/relation/{relation_id}
#
#             POST-params:
#                 members: sequence of RIDs, at least 2 of them. Like members=(1,2,3)
#
#             returns same as read
#         """
#         relation_id = self.get_relation_id_from_subpath()
#         self.get_relation(relation_id)  # To check existance, will raise 404
#         rids = []
#         members = self.request.POST.getall('members')
#         if len(members) < 2:
#             raise HTTPBadRequest("'members' must have 2 or more RIDs")
#         for x in members:
#             # Just to make sure
#             resource = self.get_resource(x)
#             if resource is None:
#                 raise HTTPBadRequest("No resource found with rid %s" % x)
#             rids.append(resource.rid)
#         try:
#             self.context.relations_map[relation_id] = rids
#         except ValueError as exc:
#             raise HTTPBadRequest(exc)
#         self.request.response.status = 202  # Accepted
#         return {'relation_id': int(relation_id), 'members': list(rids)}
#
#     @view_config(request_method='DELETE')
#     def delete_relation(self):
#         """ Delete relation
#
#             /{wall}/relation/{relation_id}
#         """
#         relation_id = self.get_relation_id_from_subpath()
#         try:
#             del self.context.relations_map[relation_id]
#         except KeyError:
#             raise HTTPNotFound("No such relation")
#         self.request.response.status = 202  # Accepted
#         return {'deleted': relation_id}
#
#     @view_config(name='list_relations', request_method='GET')
#     def list_contained_relations(self):
#         """ List all contained relations within this wall.
#
#             /{wall}/list_relations
#
#             Returns a list of all relations in the same structure as the read function.
#         """
#         contained_rids = self.root.rid_map.contained_rids(self.context)
#         results = []
#         for relation_id in self.context.relations_map.find_relevant_relation_ids([self.context.rid] + list(contained_rids)):
#             results.append(
#                 {'relation_id': relation_id, 'members': list(self.context.relations_map[relation_id])}
#             )
#         return results
#
#     @view_config(request_method='OPTIONS')
#     def preflight_options_requests(self):
#         """ Simply return 200 ok for OPTIONS-requests. """
#         # FIXME: Send a debug message?
#         return {}