from cornice.resource import resource, view
from cornice.validators import colander_validator

from kedja.views.api.base import ResourceAPIBase, RIDPathSchema


@resource(path='/api/1/walls/{rid}', collection_path='/api/1/walls',
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
        # FIXME: json decoding errors
        appstruct = self.request.json_body
        # Note: The mutator API will probably change!
        with self.request.get_mutator(new_res) as mutator:
            changed = mutator.update(appstruct)
        # self.request.response.status = 202  # Accepted
        return {'changed': list(changed)}
