from logging import getLogger

from arche.objectmap.rid_map import ResourceIDMap
from kedja.models.relations import RelationMap


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
        app_root.relations_map = RelationMap()
        return app_root
