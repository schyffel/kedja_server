from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from translationstring import TranslationStringFactory

from .models.appmaker import appmaker


_ = TranslationStringFactory('kedja')


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root(), request)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        config.include('kedja')
        config.include('.views')
    return config.make_wsgi_app()


def includeme(config):
    """ Include all locals except views. Useful for integration/functional tests too. """
    # Pyramid/Pylons
    config.registry.settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'
    config.include('pyramid_tm')
    config.include('pyramid_retry')
    config.include('pyramid_zodbconn')
    config.set_root_factory(root_factory)
    config.include('pyramid_chameleon')
    # Cornice
    config.include('cornice')
    config.include('cornice_swagger')
    # Arche modules - note: will change!
    config.include('arche.predicates')
    config.include('arche.request_methods')
    config.include('arche.content')
    config.include('arche.mutator')
    config.include('arche.schemas')
    # Internal
    config.include('.models')
    config.include('.resources')
