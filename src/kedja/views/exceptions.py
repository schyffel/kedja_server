from colander import Invalid
from pyramid.view import exception_view_config


@exception_view_config(context=Invalid, renderer='json', tm_active=True)
def handle_invalid(exc, request):
    """ Cause colander.Invalid to work like a HTTPError."""
    request.response.status_int = 400
    request.response.json=exc.asdict(translate=request.localizer.translate)
    return request.response


def includeme(config):
    config.scan(__name__)
