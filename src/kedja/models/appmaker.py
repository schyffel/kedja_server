from logging import getLogger


logger = getLogger(__name__)


def appmaker(zodb_root, request):
    try:
        return zodb_root['app_root']
    except KeyError:
        logger.info("Creating root")
        zodb_root['app_root'] = root = request.registry.content('Root')
        root_populator(root, request)
        return root


def root_populator(root, request):
    """ Populates the application root with the basics.
    """
    root['users'] = request.registry.content('Users')
