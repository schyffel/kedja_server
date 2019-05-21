from cornice.resource import resource
from cornice.validators import colander_validator
from cornice.resource import view

from kedja.views.api.base import SubResourceAPISchema
from kedja.views.api.base import ResourceAPIBase
from kedja.views.api.base import ResourceAPISchema


@resource(collection_path='/api/1/walls/{rid}/collections',
          path='/api/1/walls/{rid}/collections/{subrid}',  # This isn't used, but cornice needs  this path?
          tags=['Collections'],
          schema=SubResourceAPISchema(),
          validators=(colander_validator,),
          cors_origins=('*',),
          factory='kedja.root_factory')
class ContainedCollectionsAPI(ResourceAPIBase):
    type_name = 'Collection'
    parent_type_name = 'Wall'

    def get(self):
        # wall = self.base_get(self.request.matchdict['rid'], type_name=self.parent_type_name)
        # Do what with wall?
        return self.base_get(self.request.matchdict['subrid'], type_name=self.type_name)

    # FIXME schemas?
    def put(self):
        return self.base_put(self.request.matchdict['subrid'], type_name=self.type_name)

    def delete(self):
        return self.base_delete()

    @view(schema=ResourceAPISchema())
    def collection_get(self):
        return list(self.context.values())

    @view(schema=ResourceAPISchema())
    def collection_post(self):
        return self.base_collection_post(self.type_name, parent_rid=self.request.matchdict['rid'], parent_type_name=self.parent_type_name)

    def options(self):
        # FIXME:
        return {}


def includeme(config):
    config.scan(__name__)
