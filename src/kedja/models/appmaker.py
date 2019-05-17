from logging import getLogger


logger = getLogger(__name__)


def appmaker(zodb_root, request):
    try:
        return zodb_root['app_root']
    except KeyError:
        logger.info("Creating root")
        cf = request.registry.content
        zodb_root['app_root'] = root = cf('Root')
        root['users'] = cf('Users')
        return root
