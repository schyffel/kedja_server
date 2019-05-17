from cornice_swagger import CorniceSwagger
from cornice.service import get_services, Service


# Create a service to serve our OpenAPI spec
swagger = Service(name='OpenAPI',
                  path='/openapi.json',
                  description="OpenAPI documentation")


@swagger.get()
def openAPI_spec(request):
    doc = CorniceSwagger(get_services())
    my_spec = doc.generate('Kedja API', '1.0.0')
    return my_spec


def includeme(config):
    config.scan(__name__)
