import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IUser
from kedja.security import PERSONAL
from kedja.resources.security import SecurityAwareMixin
from kedja.resources.json import JSONRenderable


class UserSchema(colander.Schema):
    first_name = colander.SchemaNode(
        colander.String(),
        title = "First name",
        missing=colander.drop,
    )
    last_name = colander.SchemaNode(
        colander.String(),
        title = "Last name",
        missing=colander.drop,
    )
    email = colander.SchemaNode(
        colander.String(),
        title = "Email",
        validator = colander.Email(),
        missing=colander.drop,
    )
    picture = colander.SchemaNode(
        colander.String(),
        title = "Profile picture url",
        validator = colander.url,
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(IUser)
class User(Folder, JSONRenderable, SecurityAwareMixin):
    acl_name = 'user'

    def __init__(self, **kw):
        super().__init__(**kw)
        assert 'rid' in kw, "rid is a required argument when constructing User objects"
        self.add_user_roles(kw['rid'], PERSONAL)

    @property
    def userid(self):
        return str(self.rid)


UserContent = ContentType(factory=User, schema=UserSchema, title=_("User"))

UserPerms = UserContent.permissions


def includeme(config):
    config.add_content(UserContent)
