from arche.interfaces import IFolder
from arche.interfaces import IRoot  # API
from zope.interface import Interface, Attribute


class ICredentials(Interface):
    pass

class ICard(IFolder):
    pass

class ICollection(IFolder):
    pass

class IWall(IFolder):
    pass

class IUsers(IFolder):
    pass

class IUser(IFolder):
    pass


class IAuthomatic(Interface):
    """ The util where authomatic is configured.
    """


class IOneTimeRegistrationToken(Interface):
    """ When an incoming authentication finds no corresponding user, store the information temporarily
        under a token and send that token to a registration form.

        If the registration is completed, retrieve the information and create a user.
    """


class IOneTimeAuthToken(Interface):
    """ Stores quickly expiring tokens in redis. The purpose is to never have to share the actual login header
        via a 302 redirect.

        The value is the header needed to authenticate. a typical stored key might look something like this:

        Key: 'otat.<userid>.<credentials token>
        Value: 'Basic <base64 encoded token here>'
    """
    context = Attribute("The adapted context, should be the Root.")
    prefix = Attribute("Prefix redis keys with this.")

    def __init__(context):
        pass

    def get_key(credentials: ICredentials, token:str):
        """ Return redis key """


    def create(credentials: ICredentials, expires=30, registry=None):
        """ Create and store a token. Returns the token.
        """

    def consume(userid:str, token:str, registry=None):
        """ Consume token and return the real auth header.
        """
