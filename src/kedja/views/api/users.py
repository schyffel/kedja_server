import colander
from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_validator

from kedja.resources.user import UserSchema
from kedja.views.api.base import ResourceAPISchema
from kedja.views.api.base import ResourceAPIBase


class UpdateUserAPISchema(ResourceAPISchema):
    title = "Update a specific user"
    body = UserSchema(description="JSON payload")


@resource(path='/api/1/users/{rid}',
          collection_path='/api/1/users',
          #response_schemas=response_schemas,
          validators=(colander_validator,),
          cors_origins=('*',),
          tags=['Users'],
          factory='kedja.root_factory')
class UsersAPIView(ResourceAPIBase):
    """ Create update or remove users """
    type_name = 'User'
    parent_type_name = 'Users'

    # def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'view_resource_validator'))
    def get(self):
        return self.base_get(self.request.matchdict['rid'], type_name=self.type_name)

    @view(schema=UpdateUserAPISchema(), validators=(colander_validator, 'edit_resource_validator'))
    def put(self):
        return self.base_put(self.request.matchdict['rid'], type_name=self.type_name)

    @view(schema=ResourceAPISchema(), validators=(colander_validator, 'delete_resource_validator'))
    def delete(self):
        return self.base_delete(self.request.matchdict['rid'], type_name=self.type_name)

    @view(schema=None)
    def collection_get(self):
        return self.base_collection_get(self.context['users'], type_name=self.type_name)

#    @view(schema=CreateUserAPISchema())
#    def collection_post(self):
#        return self.base_collection_post(self.type_name,
#                                         parent_rid=self.context['users'].rid,
#                                         parent_type_name=self.parent_type_name)


def includeme(config):
    config.scan(__name__)
