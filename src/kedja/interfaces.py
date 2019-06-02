from arche.interfaces import IFolder
from arche.interfaces import IRoot  # API
from zope.interface import Interface


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