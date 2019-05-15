from cornice import Service
from cornice.validators import colander_body_validator


# def dynamic_schema(request):
#     if request.method == 'POST':
#         schema = foo_schema()
#     elif request.method == 'PUT':
#         schema = bar_schema()
#     return schema
#
#
# def my_validator(request, **kwargs):
#     kwargs['schema'] = dynamic_schema(request)
#     return colander_body_validator(request, **kwargs)


#@service.post(validators=(my_validator,))
#def post(request):
#    return request.validated



from cornice.resource import resource as cornice_resource
from cornice.resource import view as cornice_view
from kedja.resources.wall import WallContent

from pyramid.traversal import resource_path


class ResourceAPIBase(object):

    def __init__(self, request, context=None):
        self.request = request
        self.context = context
        self._lookup_cache = {}

    def get_resource(self, rid):
        if isinstance(rid, str):
            rid  = int(rid)
        return self._lookup_cache.setdefault(rid, self.request.root.rid_map.get_resource(rid))

    def error(self, request, msg="Doesn't exist", type='path', status=404):
        request.errors.add(type, msg)
        request.errors.status = status

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict.get('type_name', object())
        if type_name not in request.registry.content:
            return self.error(request, msg="'type_name' specified doesn't exist.")

    def validate_rid(self, request, **kw):
        """ RID must be numeric and exist. """
        try:
            rid = int(self.request.matchdict['rid'])
        except ValueError:
            return self.error(request, "rid must be numeric", status=400)
        if self.get_resource(rid) is None:
            return self.error(request, "No resource with that rid exists")

    def validate_rid_to_type_name(self, request, **kw):
        try:
            rid = int(self.request.matchdict['rid'])
        except ValueError:
            rid = object()
        resource = self.get_resource(rid)
        if resource is None:
            return self.error(request, "resource not found")
        type_name = request.matchdict['type_name']
        if resource.type_name != type_name:
            return self.error(request, "resource is not a '%s'" % type_name)

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict['type_name']
        if type_name not in request.registry.content:
            return self.error(request, "No resource called %s" % type_name)


# Cornice doesn't respect pyramids root factory - beware!
@cornice_resource(collection_path='/api/{type_name}', path='/api/{type_name}/{id}',
                  validators=('validate_type_name',), factory='kedja.root_factory')
class ResourceAPI(ResourceAPIBase):
    """ Resources"""

#RID:  -3839708759738202385
    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def collection_get(self):
        """ Fetch all content types viewable with this user?"""
        return {'type_name': self.request.matchdict['type_name'], 'note': 'will return your resources'}
        #return {'users': _USERS.keys()}

    @cornice_view(validators=('validate_rid', 'validate_type_name', 'validate_rid_to_type_name'))
    def get(self):
        """ Get specific resource """
        return self.get_resource(self.request.matchdict['id'])

    @cornice_view(validators=('validate_rid', 'validate_type_name', 'validate_rid_to_type_name'))
    def delete(self):
        """ Delete a resource """
        rid = self.request.matchdict['rid']
        resource = self.get_resource(rid)
        parent = resource.__parent__
        parent.remove(resource.__name__)
        return {'removed': rid}

 #   def collection_post(self):
  #      pass
       #print(self.request.json_body)
       #_USERS[len(_USERS) + 1] = self.request.json_body
       #return True

WallContent.schema





#@cornice_resource(path='/api/create/${type_name}/at/{rid}',
#                  validators=('validate_type_name',),
#                  factory='kedja.root_factory')
@cornice_resource(path='/api/create/${type_name}/at/{rid}',
                  factory='kedja.root_factory')
class CreateResourceAPI(ResourceAPIBase):
    """ Create differs a bit since it needs to know where to create something. """

    def validate_type_name(self, request, **kw):
        type_name = request.matchdict['type_name']
        if type_name not in request.registry.content:
            return self.error(request, "No resource called %s" % type_name)

    def create_schema_validator(self, request, **kw):
        type_name = self.request.matchdict['type_name']
        parent_rid = self.request.matchdict['rid']
        parent = self.get_resource(parent_rid)
        kw['schema'] = request.registry.content.get_schema(type_name, parent=parent, request=request)
        return colander_body_validator(request, **kw)

    @cornice_view(validators=('validate_rid', 'validate_type_name', 'create_schema_validator'))
    def post(self):
        """ Create a new resource. Attach it to the resource tree. Then update it. """
        type_name = self.request.matchdict['type_name']
        parent_rid = self.request.matchdict['rid']
        parent = self.get_resource(parent_rid)
        new_resource = self.request.registry.content(type_name)




# @cornice_resource(path='/api/{type_name}/create_at/{rid}',
#                   validators=('validate_type_name',),
#                   factory='kedja.root_factory')
# class CreateResourceAPI(ResourceAPIBase):
#     """ Create differs a bit since iti needs to know where to create something. """
#
#     @cornice_view(validators=('validate_id',))
#     def post(self):
#         """ Create a new resource. Attach it to the resource tree. Then update it. """
#         type_name = self.request.matchdict['type_name']
#         parent_rid = self.request.matchdict['rid']
#         parent = self.get_resource(parent_rid)
#         resource = self.request.registry.content(type_name)





"""
URL	Description
/api	The API entry point
/api/:coll	A top-level collection named “coll”
/api/:coll/:id	The resource “id” inside collection “coll”
/api/:coll/:id/:subcoll	Sub-collection “subcoll” under resource “id”
/api/:coll/:id/:subcoll/:subid	The resource “subid” inside “subcoll”

GET	collection	Retrieve all resources in a collection
GET	resource	Retrieve a single resource
HEAD	collection	Retrieve all resources in a collection (header only)
HEAD	resource	Retrieve a single resource (header only)
POST	collection	Create a new resource in a collection
PUT	resource	Update a resource
PATCH	resource	Update a resource
DELETE	resource	Delete a resource
OPTIONS	any	Return available HTTP methods and other options
"""

def includeme(config):
    config.scan(__name__)
