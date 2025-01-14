import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator

from kedja.resources.wall import WallSchema
from kedja.views.api.base import BaseResponseAPISchema
from kedja.views.api.base import ResourceAPISchema
from kedja.views.api.base import ResourceAPIBase


class WallBodyAPISchema(BaseResponseAPISchema):
    data = WallSchema()


class ResponseSchema(colander.Schema):
    title = "Wall"
    body = WallBodyAPISchema()


class CreateWallSchema(colander.Schema):
    title = "Create a new wall"
    body = WallSchema(description="JSON payload")


class UpdateWallAPISchema(ResourceAPISchema, CreateWallSchema):
    title = "Update a specific wall"


response_schemas = {
    '200': ResponseSchema(description='Return resource'),
    '202': ResponseSchema(description='Return resource'),
    '201': ResponseSchema(description='Return resource'),
}


@resource(path='/api/1/walls/{rid}',
          collection_path='/api/1/walls',
          response_schemas=response_schemas,
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallsAPIView(ResourceAPIBase):
    """ Resources """
    type_name = 'Wall'
    parent_type_name = 'Root'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'view_resource_validator'))
    def get(self):
        return self.base_get(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=UpdateWallAPISchema(), validators=(colander_validator, 'edit_resource_validator'))
    def put(self):
        return self.base_put(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'delete_resource_validator'))
    def delete(self):
        return self.base_delete(self.request.matchdict['rid'], type_name='Wall')

    @view(schema=None)
    def collection_get(self):
        return self.base_collection_get(self.context, type_name=self.type_name)

    @view(schema=CreateWallSchema())
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=1, parent_type_name=self.parent_type_name)


@resource(path='/api/1/walls/{rid}/structure',
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallStructureAPIView(ResourceAPIBase):
    type_name = 'Wall'

    @view(schema=ResourceAPISchema())
    def get(self):
        """
        Return a structure with all contained items. It has to be a list since we want to keep order.

        It could look something like this:
        [
            [10, [
                [101, []], [201, []], [301, []]
            ]],
            [20, [
                [102, []], [202, []], [302, []]
            ]],
            [30, [
                [103, []], [203, []], [303, []]
            ]]
        ]
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            results = []
            self.get_structure(wall, results)
            return results

    def get_structure(self, context, data):
        for v in context.values():
            contained_data = []
            data.append([v.rid, contained_data])
            self.get_structure(v, contained_data)


@resource(path='/api/1/walls/{rid}/content',
          # validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Walls'],
          factory='kedja.root_factory')
class WallContentAPIView(ResourceAPIBase):
    type_name = 'Wall'

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'view_resource_validator'))
    def get(self):
        """ Get a structure with all of the content within this wall.
            It returns a dict where the resource ID is the key.
        """
        wall = self.base_get(self.request.matchdict['rid'], type_name='Wall')
        if wall:
            results = {}
            self.get_content(wall, results)
            # Load relations etc too
            return {'resources': results}

    def get_content(self, context, data):
        for v in context.values():
            data[v.rid] = v
            self.get_content(v, data)


def includeme(config):
    config.scan(__name__)
