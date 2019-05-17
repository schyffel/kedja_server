import colander
from cornice.resource import resource, view
from cornice.validators import colander_validator
from kedja.resources.wall import WallSchema

from kedja.views.api.base import BaseResponseSchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import RIDPathSchema


class WallBodySchema(BaseResponseSchema):
    data = WallSchema()


class ResponseSchema(colander.Schema):
    title = "Wall"
    body = WallBodySchema()


response_schemas = {
    '200': ResponseSchema(description='Return value'),
    '202': ResponseSchema(description='Return value')
}


@resource(path='/api/1/walls/{rid}', collection_path='/api/1/walls',
            response_schemas=response_schemas,
          tags=['Walls'], factory='kedja.root_factory')
class WallsAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    @view(validators=('validate_rid', colander_validator), schema=RIDPathSchema())
    def get(self):
        resource = self.base_get()
        # FIXME: Check type
        return resource

    @view(validators=('validate_rid', colander_validator), schema=RIDPathSchema())
    def put(self):
        return self.base_put()

    @view(validators=('validate_rid', colander_validator), schema=RIDPathSchema())
    def delete(self):
        return self.base_delete()

    def collection_get(self):
        return list(self.context.values())

    def collection_post(self):
        new_res = self.request.registry.content("Wall")
        new_res.rid = self.root.rid_map.new_rid()
        # Should be the root
        self.context.add(str(new_res.rid), new_res)
        appstruct = self.get_json_appstruct()
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        return {'changed': list(changed)}
