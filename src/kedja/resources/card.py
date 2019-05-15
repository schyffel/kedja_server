import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICard
from kedja.resources.mixins import JSONRenderable


class CardSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
    )


@implementer(ICard)
class Card(Folder, JSONRenderable):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.order = ()  # Enable ordering


CardContent = ContentType(factory=Card, schema=CardSchema, title=_("Card"))


def includeme(config):
    config.add_content(CardContent)
