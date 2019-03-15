
def appmaker(zodb_root, request):
    if 'app_root' not in zodb_root:
        app_root = MyModel()
        zodb_root['app_root'] = app_root
    return zodb_root['app_root']
