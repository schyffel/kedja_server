import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IWall
from kedja.models.relations import RelationMap
from kedja.resources.mixins import JSONRenderable


class WallSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(IWall)
class Wall(Folder, JSONRenderable):
    title = ""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.relations_map = RelationMap()
        self.order = ()  # Enable ordering


WallContent = ContentType(factory=Wall, schema=WallSchema, title=_("Wall"))


def includeme(config):
    config.add_content(WallContent)
