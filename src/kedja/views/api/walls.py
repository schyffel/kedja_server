import colander
from cornice.resource import resource, view
from cornice.validators import colander_validator
from kedja.resources.wall import WallSchema

from kedja.views.api.base import BaseResponseSchema
from kedja.views.api.base import ResourceSchema
from kedja.views.api.base import ResourceAPIBase


class WallBodySchema(BaseResponseSchema):
    data = WallSchema()


class ResponseSchema(colander.Schema):
    title = "Wall"
    body = WallBodySchema()


class CreateWallSchema(colander.Schema):
    title = "Create a new wall"
    body = WallSchema(description="JSON payload")


class UpdateWallSchema(ResourceSchema, CreateWallSchema):
    title = "Update a specific wall"


response_schemas = {
    '200': ResponseSchema(description='Return resource'),
    '202': ResponseSchema(description='Return resource'),
    '201': ResponseSchema(description='Return resource'),
}


@resource(path='/api/1/walls/{rid}',
          collection_path='/api/1/walls',
          response_schemas=response_schemas,
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallsAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    @view(validators=('validate_rid', colander_validator), schema=ResourceSchema())
    def get(self):
        resource = self.base_get()
        # FIXME: Check type
        return resource

    @view(validators=('validate_rid', colander_validator), schema=UpdateWallSchema())
    def put(self):
        return self.base_put()

    @view(validators=('validate_rid', colander_validator), schema=ResourceSchema())
    def delete(self):
        return self.base_delete()

    def collection_get(self):
        return list(self.context.values())

    @view(schema=CreateWallSchema())
    def collection_post(self):
        new_res = self.request.registry.content("Wall")
        new_res.rid = self.root.rid_map.new_rid()
        # Should be the root
        self.context.add(str(new_res.rid), new_res)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            mutator.update(appstruct)
        return new_res

    def options(self):
        # FIXME:
        return {}
