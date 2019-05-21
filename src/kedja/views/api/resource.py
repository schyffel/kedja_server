
from cornice.resource import resource
from cornice.validators import colander_validator

from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


# Cornice doesn't respect pyramids root factory - beware!
@resource(path='/api/1/rid/{rid}',
          schema=ResourceAPISchema(),
          tags=['Any resource'],
          cors_origins=('*',),
          validators=(colander_validator, 'validate_rid'), factory='kedja.root_factory')
class ResourceAPI(ResourceAPIBase):
    """ Resources """

    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def get(self):
        return self.base_get(self.request.matchdict['rid'])

    def put(self):
        return self.base_put(self.request.matchdict['rid'])

    def delete(self):
        return self.base_delete(self.request.matchdict['rid'])

    def options(self):
        # FIXME:
        return {}


def includeme(config):
    config.scan(__name__)
