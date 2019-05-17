from cornice.resource import resource
from cornice.validators import colander_validator

from kedja.views.api.base import SubRIDPathSchema, ContainedAPI


@resource(collection_path='/api/1/collections/{rid}/cards',
          path='/api/1/collections/{rid}/cards/{subrid}',  # This isn't used, but cornice needs  this path?
          tags=['Cards'],
          schema=SubRIDPathSchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCardsAPI(ContainedAPI):
    create_type = 'Card'
