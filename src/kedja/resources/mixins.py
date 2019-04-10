
# FIXME: This is of course a stub :)

class JSONRenderable(object):

    def __json__(self, request):
        return {'type_name': self.type_name, 'rid': self.rid}
