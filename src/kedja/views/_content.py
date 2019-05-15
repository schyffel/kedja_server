

class BaseAPIView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request




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

class RestView(BaseAPIView):
    """ Collection as in the restful idea of collection.
    """


    def get_collection(self):
        pass

    def get_resource(self):
        pass

    def post(self):
        """ AKA create a new resource within another parent. """

    def post(self):
        pass


class RestCreateView(BaseAPIView):




@cornice_resource(collection_path='/api/{type_name}', path='/api/{type_name}/{id}',
                  validators=('validate_type_name',))
class ResourceAPI(object):

    def __init__(self, request, context=None):
        self.request = request
        # context here is an instance of this view class. Gah!



#RID:  -3839708759738202385
    #def __acl__(self):
    #    return [(Allow, Everyone, 'everything')]

    def collection_get(self):
        """ Fetch all content types viewable with this user?"""
        return {'type_name': self.request.matchdict['type_name']}
        #return {'users': _USERS.keys()}

    @cornice_view(validators=('validate_id'))
    def get(self):
        return self.request.root.rid_map.get_resource(self.request.matchdict['id'])


    def collection_post(self):
        print(self.request.json_body)
        _USERS[len(_USERS) + 1] = self.request.json_body
        return True

    def validate_type_name(self, request, **kw):
        print(kw)
        type_name = request.matchdict.get('type_name', object())
        if type_name not in request.registry.content:
            return self._error(request, msg="'type_name' specified doesn't exist.")

    def validate_id(self, request, **kw):
        import pdb;pdb.set_trace()

        try:
            rid = int(self.request.matchdict['id'])
        except TypeError:
            return self._error(request, "id must be numeric", status=400)
        resource = self.request.root.rid_map.get_resource(rid)
        if resource is None:
            return self._error(request, "resource not found")
        type_name = request.matchdict['type_name']
        if resource.type_name != type_name:
            return self._error(request, "resource is not a '%s'" % type_name)



    def _error(self, request, msg="Doesn't exist", type='path', status=404):
        request.errors.add(type, msg)
        request.errors.status = status



def includeme(config):


    config.scan(__name__)
