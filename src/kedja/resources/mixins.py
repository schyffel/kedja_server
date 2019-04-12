
# FIXME: This is of course a stub :)

class JSONRenderable(object):

    def __json__(self, request):
        with request.get_mutator(self) as mutator:
            appstruct = mutator.appstruct()
        return {'type_name': self.type_name, 'rid': self.rid, 'data': appstruct}
