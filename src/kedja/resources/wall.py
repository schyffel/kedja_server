import colander
from arche.folder import Folder
from arche.content import ContentType
from kedja.permissions import INVITE, VISIBILITY
from pyramid.security import DENY_ALL
from zope.interface import implementer

from kedja import _
from kedja.interfaces import IWall
from kedja.models.relations import RelationMap
from kedja.resources.json import JSONRenderable
from kedja.resources.security import SecurityAwareMixin


class WallSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_("Title"),
        missing=colander.drop,
    )

    def after_bind(self, node, kw):
        """ Use this instead of deferred, since cornice can't handle schema binding. """
        pass


@implementer(IWall)
class Wall(Folder, JSONRenderable, SecurityAwareMixin):
    title = ""
    acl_name = 'private_wall'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.relations_map = RelationMap()
        self.order = ()  # Enable ordering

    # def __acl__(self):
    #     acl = self.get_context_acl()
    #     acl.extend(self.__parent__.get_context_acl())
    #     acl.append(DENY_ALL)
    #     return acl


WallContent = ContentType(factory=Wall, schema=WallSchema, title=_("Wall"))
WallContent.add_permission_type(INVITE)
WallContent.add_permission_type(VISIBILITY)

WallPerms = WallContent.permissions


def includeme(config):
    config.add_content(WallContent)
