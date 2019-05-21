import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IUser
from kedja.resources.mixins import JSONRenderable


class UserSchema(colander.Schema):
    first_name = colander.SchemaNode(
        colander.String(),
        title = _("First name"),
    )
    last_name = colander.SchemaNode(
        colander.String(),
        title = _("Last name"),
    )
    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass

@implementer(IUser)
class User(Folder, JSONRenderable):

    @property
    def userid(self):
        return self.rid


UserContent = ContentType(factory=User, schema=UserSchema, title=_("User"))


def includeme(config):
    config.add_content(UserContent)
