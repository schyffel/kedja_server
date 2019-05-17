
from cornice.resource import resource
from cornice.validators import colander_validator

from kedja.views.api.base import ResourceAPIBase, ResourceSchema


# Cornice doesn't respect pyramids root factory - beware!
@resource(path='/api/1/rid/{rid}', schema=ResourceSchema(), tags=['Any resource'],
                  validators=(colander_validator, 'validate_rid'), factory='kedja.root_factory')
class ResourceAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def get(self):
        return self.base_get()

    def put(self):
        return self.base_put()

    def delete(self):
        return self.base_delete()


def includeme(config):
    config.scan(__name__)