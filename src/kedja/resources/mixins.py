
# FIXME: This is of course a stub :)

class JSONRenderable(object):

    def __json__(self, request):
        with request.get_mutator(self) as mutator:
            appstruct = mutator.appstruct()
        return {'type_name': request.registry.content.get_type(self), 'rid': str(self.rid), 'data': appstruct}
