from logging import getLogger
from uuid import uuid4

import yaml
from authomatic import Authomatic
from pyramid.exceptions import ConfigurationError

from kedja.interfaces import IAuthomatic


logger = getLogger(__name__)


def includeme(config):
    """
        The authomatic config should look something like this:
        'fb': {

        'class_': authomatic.providers.oauth2.Facebook,

        # Facebook is an AuthorizationProvider too.
        'consumer_key': '########################',
        'consumer_secret': '########################',

        # But it is also an OAuth 2.0 provider and it needs scope.
        'scope': ['user_about_me', 'email', 'publish_stream'],
    },

        So we need to resolve the 'class_' part for whatever we have configured.

        For this project we'll also keep the secret within this file
    """
    authomatic_file = config.registry.settings.get('kedja.authomatic', '')
    if authomatic_file:
        with open(authomatic_file, 'r') as f:
            auth_config = yaml.safe_load(f)

        secret = auth_config.pop('secret', None)
        if secret is None:
            logger.warning("'secret' is missing within the automatic configuration. A random secret will be used.")
            secret = str(uuid4())
        # Fix all class names within the configuration
        for k, section in auth_config.items():
            if 'class_' in section:
                section['class_'] = config.maybe_dotted(section['class_'])
            else:
                raise ConfigurationError("The section '%s' lacks the 'class_' key which is required." % k)
        authomatic = Authomatic(config=auth_config, secret=secret)
        config.registry.registerUtility(authomatic, IAuthomatic)
        logger.debug("Registered authomatic with providers: '%s'" % ", ".join(auth_config.keys()))
    else:
        logger.warning("'kedja.authomatic' is missing in the paster.ini file. "
                       "It should point to a yaml file with Authomatic configuration. "
                       "Login with authomatic will be disabled!")
