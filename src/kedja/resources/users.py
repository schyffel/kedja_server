import colander
from arche.folder import Folder
from arche.content import ContentType
from pyramid.traversal import find_root
from zope.interface import implementer
from BTrees.OOBTree import OOBTree
from BTrees.OLBTree import OLBTree

from kedja import _
from kedja.interfaces import IUser
from kedja.interfaces import IUsers
from kedja.resources.json import JSONRenderable


class UsersSchema(colander.Schema):
    pass


@implementer(IUsers)
class Users(Folder, JSONRenderable):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.providers = OOBTree()

    def add_provider(self, user, userpayload:dict):
        """
        :param user: A Kedja User object
        :param userpayload: the result from the authomatic login, the user part as a dict
        """
        provider = self.providers.setdefault(userpayload['provider'], OLBTree())
        provider[userpayload['id']] = user.rid

    def find_providers_user(self, result, default=None):
        """
        :param result: Authomatic login result
        :param default: Return value when not found
        :return: User or default
        """
        user_rid = self.providers.get(result.provider.name, {}).get(result.user.id, None)
        return self.get_rid_user(user_rid, default)

    def get_rid_user(self, rid, default=None):
        """
        :param rid: Users RID (resource  ID)
        :param default: Return value when not found
        :return: User or default
        """
        root = find_root(self)
        user = root.rid_map.get_resource(rid, default)
        if IUser.providedBy(user):
            return user
        return default


UsersContent = ContentType(factory=Users, schema=UsersSchema, title=_("Users"))


def includeme(config):
    config.add_content(UsersContent)
