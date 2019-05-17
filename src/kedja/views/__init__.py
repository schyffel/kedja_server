
def includeme(config):
#    config.include('._deprecated_api')
    config.include('.api')
    config.include('.api_cornice')
    config.include('.exceptions')
    config.include('.openapi')