from logging import getLogger


logger = getLogger(__name__)


def appmaker(zodb_root, request):
    try:
        return zodb_root['app_root']
    except KeyError:
        logger.info("Creating root")
        zodb_root['app_root'] = root = request.registry.content.create('Root')
        return root
