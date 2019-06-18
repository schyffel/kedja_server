import json
from random import choice
from string import ascii_letters, digits

from arche.interfaces import IRoot
from kedja.utils import get_redis_conn
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authentication import extract_http_basic_credentials
from pyramid.interfaces import IAuthenticationPolicy
from zope.component import adapter
from zope.interface import implementer

from kedja.interfaces import ICredentials, IOneTimeRegistrationToken
from kedja.interfaces import IOneTimeAuthToken


@implementer(IAuthenticationPolicy)
class HTTPHeaderAuthenticationPolicy(CallbackAuthenticationPolicy):
    """ An authentication policy that fetches authentication objects from the user profile.
        It will decode a basic HTTP header
    """

    def __init__(self, callback=None, debug=False):
        self.callback = callback
        self.debug = debug

    def remember(self, request, userid, root=None, token=None, **kw):
        if root is None:
            root = request.root
        user = root['users'][userid]
        cred = request.registry.content('Credentials', user, token=token, registry=request.registry)
        user.add_credentials(cred)
        return cred

    def forget(self, request):
        token_userid, token = extract_http_basic_credentials(request)
        if token_userid and request.root:
            request.root['users'][token_userid].remove_credentials(token)

    def unauthenticated_userid(self, request):
        token_userid, token = extract_http_basic_credentials(request)
        users = request.root['users']
        if token_userid in users:
            user = users[token_userid]
            if user.validate_credentials(token):
                return user.userid


@implementer(IOneTimeRegistrationToken)
@adapter(IRoot)
class OneTimeRegistrationToken(object):
    __doc__ = IOneTimeRegistrationToken.__doc__
    prefix = 'otrt'

    def __init__(self, context: IRoot):
        self.context = context

    def get_key(self, token:str):
        return "{}.{}".format(self.prefix, token)

    def create(self, payload:dict, expires:int=1200, registry=None):
        token = _generate_token(length=50)
        conn = get_redis_conn(registry)
        key_name = self.get_key(token)
        conn.setex(key_name, expires, json.dumps(payload))
        return token

    def consume(self, token:str, registry=None):
        key_name = self.get_key(token)
        conn = get_redis_conn(registry)
        payload = conn.get(key_name)
        if payload:
            payload = payload.decode()
            return json.loads(payload)


@implementer(IOneTimeAuthToken)
@adapter(IRoot)
class OneTimeAuthToken(object):
    __doc__ = IOneTimeAuthToken.__doc__
    prefix = 'otat'

    def __init__(self, context: IRoot):
        self.context = context

    def get_key(self, credentials: ICredentials, token:str):
        return "{}.{}.{}".format(self.prefix, credentials.user.userid, token)

    def create(self, credentials: ICredentials, expires=30, registry=None):
        assert ICredentials.providedBy(credentials)  # Test
        token = _generate_token()
        conn = get_redis_conn(registry)
        key_name = self.get_key(credentials, token)
        conn.setex(key_name, expires, credentials.token)
        return token

    def consume(self, userid:str, token:str, registry=None):
        key_name = "{}.{}.{}".format(self.prefix, userid, token)
        conn = get_redis_conn(registry)
        cred_token = conn.get(key_name)
        if cred_token:
            cred_token = cred_token.decode()
            user = self.context['users'].get(userid, None)
            if user and user.validate_credentials(cred_token):
                return user.credentials[cred_token].header()

def _generate_token(length=30):
    out = ""
    for i in range(length):
        out += choice(ascii_letters + digits)
    return out




def includeme(config):
    config.registry.registerAdapter(OneTimeRegistrationToken)
    config.registry.registerAdapter(OneTimeAuthToken)
