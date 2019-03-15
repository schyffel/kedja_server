import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja.interfaces import IRoot
from kedja import _


class RootSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title = _("Title"),
    )


@implementer(IRoot)
class Root(Folder):
    """ Application root - created once. """



RootContent = ContentType(factory=Root, schema=RootSchema, title=_("Root"))


def includeme(config):
    config.add_content(RootContent)
