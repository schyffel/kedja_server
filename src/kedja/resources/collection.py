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
        title=_("Title"),
        missing="- Untitled- ",
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(ICollection)
class Collection(Folder, JSONRenderable):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.order = ()  # Enable ordering


CollectionContent = ContentType(factory=Collection, schema=CollectionSchema, title=_("Collection"))


def includeme(config):
    config.add_content(CollectionContent)
