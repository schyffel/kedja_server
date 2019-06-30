from kedja.interfaces import INamedACL


def add_acl(config, acl:INamedACL):
    assert INamedACL.providedBy(acl)
    assert acl.name
    config.registry.registerUtility(acl, name=acl.name)


def includeme(config):
    config.add_directive('add_acl', add_acl)
