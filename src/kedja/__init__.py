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
        # Pyramid/Pylons
        settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'
        config.include('pyramid_tm')
        config.include('pyramid_retry')
        config.include('pyramid_zodbconn')
        config.set_root_factory(root_factory)
        config.include('pyramid_chameleon')
        # Arche modules - note: will change!
        config.include('arche.predicates')
        config.include('arche.request_methods')
        config.include('arche.content')
        config.include('arche.schemas')
        # Internal
        config.include('.routes')
        config.include('.resources')
        config.include('.views')
    return config.make_wsgi_app()
