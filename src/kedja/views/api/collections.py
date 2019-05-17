from cornice.resource import resource
from cornice.validators import colander_validator

from kedja.views.api.base import SubRIDPathSchema, ContainedAPI


@resource(collection_path='/api/1/walls/{rid}/collections',
          path='/api/1/walls/{rid}/collections/{subrid}',  # This isn't used, but cornice needs  this path?
          tags=['Collections'],
          schema=SubRIDPathSchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCollectionsAPI(ContainedAPI):
    create_type = 'Collection'

    def options(self):
        # FIXME:
        return {}
