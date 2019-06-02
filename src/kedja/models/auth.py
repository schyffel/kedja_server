from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authentication import extract_http_basic_credentials
from pyramid.interfaces import IAuthenticationPolicy
from zope.interface import implementer


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
