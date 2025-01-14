import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICollection
from kedja.resources.json import JSONRenderable


class CollectionSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(ICollection)
class Collection(Folder, JSONRenderable):
    title = ""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.order = ()  # Enable ordering


CollectionContent = ContentType(factory=Collection, schema=CollectionSchema, title=_("Collection"))

CollectionPerms = CollectionContent.permissions


def includeme(config):
    config.add_content(CollectionContent)
