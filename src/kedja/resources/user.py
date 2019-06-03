import colander
from arche.folder import Folder
from arche.content import ContentType
from zope.interface import implementer
from BTrees.OOBTree import OOBTree

from kedja import _
from kedja.interfaces import ICredentials
from kedja.interfaces import IUser
from kedja.resources.mixins import JSONRenderable
from kedja.utils import utcnow


class UserSchema(colander.Schema):

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(IUser)
class User(Folder, JSONRenderable):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.credentials = OOBTree()

    @property
    def userid(self):
        return str(self.rid)

    def add_credentials(self, cred):
        assert ICredentials.providedBy(cred)
        if cred.user != self:
            raise ValueError("This authentication is user by another user.")
        self.credentials[cred.token] = cred

    def remove_credentials(self, token):
        if token in self.credentials:
            del self.credentials[token]

    def validate_credentials(self, token):
        if token in self.credentials:
            cred = self.credentials[token]
            return utcnow() < cred.expires


UserContent = ContentType(factory=User, schema=UserSchema, title=_("User"))


def includeme(config):
    config.add_content(UserContent)
