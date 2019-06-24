import base64
from datetime import timedelta
from logging import getLogger
from string import ascii_letters
from string import digits
from random import choice

from arche.content import ContentType
from persistent import Persistent
#from pyramid.threadlocal import get_current_registry
from zope.interface import implementer

from kedja.interfaces import ICredentials
from kedja.interfaces import IUser
from kedja.utils import utcnow
from kedja import _


_DEFAULT = object()
logger = getLogger(__name__)


def _generate_token(length=50):
    out = ""
    for i in range(length):
        out += choice(ascii_letters + digits)
    return out


@implementer(ICredentials)
class Credentials(Persistent):
    token = None
    expires = None
    user = None

    def __init__(self, user, token=None, expires=_DEFAULT, registry=None):
        #FIXME Keep registry here since we'll need it later
        #if registry is None:
        #    registry = get_current_registry()
        assert IUser.providedBy(user)
        self.user = user
        if token is None:
            token = _generate_token()
        self.token = token
        if expires is _DEFAULT:
            # FIXME Configurable from settings, request etc?
            expires = utcnow() + timedelta(days=7)
        self.expires = expires
        user.add_credentials(self)

    def __json__(self, request):
        return {'Authorization': self.header(), 'userid': self.user.userid}

    def header(self):
        merged = "%s:%s" % (self.user.userid, self.token)
        merged = bytes(merged, encoding='utf-8')
        return 'Basic %s' % base64.b64encode(merged).decode('utf-8')


CredentialsContent = ContentType(factory=Credentials, title=_("Credentials"))


def includeme(config):
    config.add_content(CredentialsContent)
