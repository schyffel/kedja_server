from logging import getLogger

from arche.objectmap.rid_map import ResourceIDMap


logger = getLogger(__name__)


def appmaker(zodb_root, request):
    try:
        return zodb_root['app_root']
    except KeyError:
        logger.info("Creating root")
        app_root = request.registry.content.create('Root')
        zodb_root['app_root'] = app_root
        app_root.rid = 1
        app_root.rid_map = ResourceIDMap(app_root)
        return app_root
