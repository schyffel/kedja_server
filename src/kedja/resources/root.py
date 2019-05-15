import colander
from arche.folder import Folder
from arche.content import ContentType
from arche.objectmap.rid_map import ResourceIDMap
from zope.interface import implementer

from kedja.resources.mixins import JSONRenderable
from kedja.interfaces import IRoot
from kedja import _


class RootSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
        validator=colander.Length(min=5, max=100),
    )


@implementer(IRoot)
class Root(Folder, JSONRenderable):
    """ Application root - created once. """

    def __init__(self):
        super().__init__()
        self.rid = 1
        self.rid_map = ResourceIDMap(self)


RootContent = ContentType(factory=Root, schema=RootSchema, title=_("Root"))


def includeme(config):
    config.add_content(RootContent)
