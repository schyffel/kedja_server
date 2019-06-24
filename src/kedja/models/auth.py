import json
from random import choice
from string import ascii_letters, digits

from arche.interfaces import IRoot
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authentication import extract_http_basic_credentials
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IDebugLogger
from zope.component import adapter
from zope.interface import implementer

from kedja.interfaces import ICredentials
from kedja.interfaces import IOneTimeAuthToken
from kedja.interfaces import IOneTimeRegistrationToken
from kedja.utils import get_redis_conn


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
        http_creds = extract_http_basic_credentials(request)

        if http_creds is None:
            self.debug and self._log(
                'No HTTP Credentials received, so no auth. Will return None',
                'authenticated_userid',
                request,
            )
            return
        if request.root is None:
            self.debug and self._log(
                "request.root is None, so can't lookup user. Will return None",
                'authenticated_userid',
                request,
            )
            return

        users = request.root['users']
        # username == userid, and password is the token for the actual credentials
        if http_creds.username in users:
            user = users[http_creds.username]
            if user.validate_credentials(http_creds.password):
                self.debug and self._log(
                    'Valid credentials and user found, will return userid "%s" ' % user.userid,
                    'authenticated_userid',
                    request,
                )
                return user.userid
            else:
                self.debug and self._log(
                    "Credentials weren't valid, will return None",
                    'authenticated_userid',
                    request,
                )
        else:
            self.debug and self._log(
                "Userid provided in credentials doesn't exist, will return None",
                'authenticated_userid',
                request,
            )


    def _log(self, msg, methodname, request):
        logger = request.registry.queryUtility(IDebugLogger)
        if logger:
            cls = self.__class__
            classname = cls.__module__ + '.' + cls.__name__
            methodname = classname + '.' + methodname
            logger.debug(methodname + ': ' + msg)



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
        token = _generate_token(length=70)
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

    def validate(self, token:str, registry=None):
        conn = get_redis_conn(registry)
        key_name = self.get_key(token)
        return bool(conn.exists(key_name))


@implementer(IOneTimeAuthToken)
@adapter(IRoot)
class OneTimeAuthToken(object):
    __doc__ = IOneTimeAuthToken.__doc__
    prefix = 'otat'

    def __init__(self, context: IRoot):
        self.context = context

    def get_key(self, userid:str, token:str):
        return "{}.{}.{}".format(self.prefix, userid, token)

    def create(self, credentials: ICredentials, expires=30, registry=None):
        assert ICredentials.providedBy(credentials)  # Test
        token = _generate_token()
        key_name = self.get_key(credentials.user.userid, token)
        conn = get_redis_conn(registry)
        conn.setex(key_name, expires, credentials.token)
        return token

    def consume(self, userid:str, token:str, registry=None):
        key_name = self.get_key(userid, token)
        conn = get_redis_conn(registry)
        cred_token = conn.get(key_name)
        if cred_token:
            cred_token = cred_token.decode()
            user = self.context['users'].get(userid, None)
            if user and user.validate_credentials(cred_token):
                return user.credentials.get(cred_token, None)

    def validate(self, userid:str, token:str, registry=None):
        key_name = self.get_key(userid, token)
        conn = get_redis_conn(registry)
        return bool(conn.exists(key_name))


def _generate_token(length=30):
    out = ""
    for i in range(length):
        out += choice(ascii_letters + digits)
    return out


def includeme(config):
    debug_authn = config.registry.settings.get('pyramid.debug_authorization', False)
    config.set_authentication_policy(HTTPHeaderAuthenticationPolicy(debug=debug_authn))
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.registry.registerAdapter(OneTimeRegistrationToken)
    config.registry.registerAdapter(OneTimeAuthToken)
