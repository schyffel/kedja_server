
from authomatic.adapters import WebObAdapter
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.security import forget
from pyramid.view import view_config

from kedja.interfaces import IAuthomatic
from kedja.views.base import BaseView


class AuthView(BaseView):

    @view_config(route_name='login', renderer='json')
    def login(self):
        # We will need the response to pass it to the WebObAdapter.
        response = Response()

        # Get the internal provider name URL variable.
        provider_name = self.request.matchdict.get('provider_name')

        authomatic = self.request.registry.queryUtility(IAuthomatic)
        if authomatic is None:
            raise HTTPBadRequest("We don't know how to process login - no providers configured.")

        # Start the login procedure.
        result = authomatic.login(WebObAdapter(self.request, response), provider_name)

        # Do not write anything to the response if there is no result!
        if result:
            # If there is result, the login procedure is over and we can write to
            # response.
            response.write('<a href="..">Home</a>')

            if result.error:
                # Login procedure finished with an error.
                response.write(
                    u'<h2>Damn that error: {0}</h2>'.format(result.error))

            elif result.user:
                # Hooray, we have the user!

                # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
                # We need to update the user to get more info.
                if not (result.user.name and result.user.id):
                    result.user.update()

                # context should be root here
                users = self.context['users']
                user = users.find_providers_user(result)
                if user is None:
                    # Register the user
                    user = self.request.registry.content('User')
                    users[user.userid] = user
                    users.add_provider(user, result)
                # Login user
                cred = self.request.registry.content('Credentials', user)
                # FIXME: Pass the token to external server, or other kind of link?
                return cred

                # Welcome the user.
                response.write(u'<h1>Hi {0}</h1>'.format(result.user.name))
                response.write(u'<h2>Your id is: {0}</h2>'.format(result.user.id))
                response.write(
                    u'<h2>Your email is: {0}</h2>'.format(result.user.email))

                # Seems like we're done, but there's more we can do...

                # If there are credentials (only by AuthorizationProvider),
                # we can _access user's protected resources.
                if result.user.credentials:

                    # Each provider has it's specific API.
                    if result.provider.name == 'fb':
                        response.write('Your are logged in with Facebook.<br />')

                        # We will access the user's 5 most recent statuses.
                        url = 'https://graph.facebook.com/{0}?fields=feed.limit(5)'
                        url = url.format(result.user.id)

                        # Access user's protected resource.
                        access_response = result.provider.access(url)

                        if access_response.status == 200:
                            # Parse response.
                            statuses = access_response.data.get('feed').get('data')
                            error = access_response.data.get('error')

                            if error:
                                response.write(
                                    u'Damn that error: {0}!'.format(error))
                            elif statuses:
                                response.write(
                                    'Your 5 most recent statuses:<br />')
                                for message in statuses:
                                    text = message.get('message')
                                    date = message.get('created_time')

                                    response.write(u'<h3>{0}</h3>'.format(text))
                                    response.write(u'Posted on: {0}'.format(date))
                        else:
                            response.write('Damn that unknown error!<br />')
                            response.write(u'Status: {0}'.format(response.status))

                    if result.provider.name == 'tw':
                        response.write('Your are logged in with Twitter.<br />')

                        # We will get the user's 5 most recent tweets.
                        url = 'https://api.twitter.com/1.1/statuses/' + \
                              'user_timeline.json'

                        # You can pass a dictionary of querystring parameters.
                        access_response = result.provider.access(url, {'count': 5})

                        # Parse response.
                        if access_response.status == 200:
                            if isinstance(access_response.data, list):
                                # Twitter returns the tweets as a JSON list.
                                response.write('Your 5 most recent tweets:')
                                for tweet in access_response.data:
                                    text = tweet.get('text')
                                    date = tweet.get('created_at')

                                    response.write(
                                        u'<h3>{0}</h3>'.format(
                                            text.replace(u'\u2026', '...')
                                        ))
                                    response.write(u'Tweeted on: {0}'.format(date))

                            elif access_response.data.get('errors'):
                                response.write(u'Damn that error: {0}!'.
                                               format(response.data.get('errors')))
                        else:
                            response.write('Damn that unknown error!<br />')
                            response.write(u'Status: {0}'.format(response.status))

        # It won't work if you don't return the response
        return response

    @view_config(route_name='logout', renderer='json')
    def logout(self):
        forget(self.request)
        return {}


#FIXME:

def home(request):
    return Response('''
        Login with <a href="login/fb">Facebook</a>.<br />
        Login with <a href="login/tw">Twitter</a>.<br />
        <form action="login/oi">
            <input type="text" name="id" value="me.yahoo.com" />
            <input type="submit" value="Authenticate With OpenID">
        </form>
    ''')


def includeme(config):
    config.add_route('login', '/login/{provider_name}')
    config.add_route('logout', '/logout')
    config.scan(__name__)
