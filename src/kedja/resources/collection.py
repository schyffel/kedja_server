import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICollection
from kedja.resources.mixins import JSONRenderable


class CollectionSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
    )


@implementer(ICollection)
class Collection(Folder, JSONRenderable):

    def __init__(self, **kw):
        self.order = ()  # Enable ordering
        super().__init__(**kw)


CollectionContent = ContentType(factory=Collection, schema=CollectionSchema, title=_("Collection"))


def includeme(config):
    config.add_content(CollectionContent)
