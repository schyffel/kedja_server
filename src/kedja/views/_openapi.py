import colander
from cornice.service import get_services
from cornice.service import Service
from cornice_swagger import CorniceSwagger


# Create a service to serve our OpenAPI spec
swagger = Service(name='OpenAPI',
                  path='/openapi_spec.json',
                  description="OpenAPI documentation")


@swagger.get()
def openAPI_spec(request):
    """ Return OpenAPI specification"""
    doc = CorniceSwagger(get_services())
    my_spec = doc.generate('Demo API', '0.1.0')
    return my_spec


def includeme(config):
    config.scan(__name__)
