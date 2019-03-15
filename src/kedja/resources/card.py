import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import ICard


class CardSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
    )


@implementer(ICard)
class Card(Folder):
    pass


CardContent = ContentType(factory=Card, schema=CardSchema, title=_("Card"))


def includeme(config):
    config.add_content(CardContent)
