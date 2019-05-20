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
          schema=ResourceSchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallsAPI(ResourceAPIBase):
    """ Resources """
    type_name = 'Wall'
    parent_type_name = 'Root'

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def get(self):
        return self.base_get(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=UpdateWallSchema())
    def put(self):
        return self.base_put(self.request.matchdict['rid'], type_name='Wall')

    def delete(self):
        return self.base_delete(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=None)
    def collection_get(self):
        return list(self.context.values())


    @view(schema=CreateWallSchema())
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=1, parent_type_name=self.parent_type_name)

    def options(self):
        # FIXME:
        return {}
