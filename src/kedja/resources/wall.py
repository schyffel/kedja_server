import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IWall


class WallSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
    )


@implementer(IWall)
class Wall(Folder):
    pass


WallContent = ContentType(factory=Wall, schema=WallSchema, title=_("Wall"))


def includeme(config):
    config.add_content(WallContent)
