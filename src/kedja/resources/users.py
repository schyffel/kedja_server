import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IUsers
from kedja.resources.mixins import JSONRenderable


class UsersSchema(colander.Schema):
    pass


@implementer(IUsers)
class Users(Folder, JSONRenderable):
    pass


UsersContent = ContentType(factory=Users, schema=UsersSchema, title=_("Users"))


def includeme(config):
    config.add_content(UsersContent)
