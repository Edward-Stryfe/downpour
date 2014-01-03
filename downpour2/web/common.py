import hashlib
import traceback
from twisted.web import resource, server
from storm import expr
from downpour2.core import VERSION, store
from downpour2.web import auth
from downpour2.sharing.store import RemoteShare


class Resource(resource.Resource, object):

    templates = {}

    def __init__(self, application, environment):
        super(Resource, self).__init__()
        self.application = application
        self.environment = environment

    def getChild(self, *args):
        c = resource.Resource.getChild(self, *args)
        if c.__class__ == resource.NoResource:
            return NotFoundResource(self.application, self.environment)
        return c

    def is_logged_in(self, request):
        user = self.get_user(request)
        if user is not None:
            return True
        return False

    def require_authentication(self, request, path):
        if not self.is_logged_in(request):
            request.redirect(path)
            return False
        return True

    def get_user(self, request):

        account = request.getSession(auth.IAccount)

        if not account.user:

            userinfo = request.getCookie('DOWNPOUR_USER')

            if userinfo:

                (userid, userhash) = userinfo.split(':', 1)
                user = self.application.store.find(
                    store.User, store.User.id == int(userid)).one()
                comphash = hashlib.md5('%s:%s' % (user.username, user.password)).hexdigest()

                if userhash == comphash:
                    account.user = user

        return account.user

    def set_user(self, user, request):

        account = request.getSession(auth.IAccount)

        if user is not None:
            userhash = hashlib.md5('%s:%s' % (user.username, user.password)).hexdigest()
            request.addCookie('DOWNPOUR_USER', '%s:%s' % (user.id, userhash), path='/')

        else:
            request.addCookie('DOWNPOUR_USER', '', path='/', expires=-1)

        account.user = user

    def render_template(self, template, request, context, content_type=None):

        unsupported = False
        ua = request.getHeader('User-Agent')
        if ua.find('MSIE 6') > -1:
            unsupported = True

        user = self.get_user(request)

        shares = self.application.store.find(
            RemoteShare, RemoteShare.user == user).order_by(
                expr.Asc(RemoteShare.name))

        defaults = {
            'version': VERSION,
            'unsupported': unsupported,
            'user': user,
            'shares': shares,
            'paused': self.application.paused,
            'notifications': self.application.alerts.unread(),
            'standalone': request.requestHeaders.hasHeader('X-Standalone-Content')
        }

        defaults.update(context)

        # Hack for jinja2 <= 2.7.1 - PrefixLoader doesn't propagate globals
        defaults.update(self.environment.globals)

        try:
            t = self.environment.get_template(template)
        except Exception as e:
            traceback.print_exc()
            return self.render_error(request, defaults, 'Template Not Found',
                                     'Could not load page template: %s' % template)

        if content_type:
            request.setHeader('Content-type', content_type)
        else:
            request.setHeader('Content-type', 'text/html; charset=UTF-8')

        return t.render(defaults).encode('utf8')

    def render_error(self, request, context, title, message):

        try:
            # Check for existence first so we don't go into a loop
            self.environment.get_template('core/errors/error.html')
            return self.render_template('core/errors/error.html', request, context.update({
                'title': title,
                'message': message
            }))

        except Exception:
            return '<h1>%s</h1><p>%s</p><p>%s</p>' % (
                title, message, 'Additionally, the error page template could not be found.')


class AuthenticatedResource(Resource):

    def render(self, request):
        if not self.is_logged_in(request):
            request.redirect('/account/login')
            request.finish()
            return server.NOT_DONE_YET
        return Resource.render(self, request)


class AdminResource(Resource):

    def render(self, request):

        user = self.get_user(request)

        if not user:
            request.redirect('/account/login')
            request.finish()
            return server.NOT_DONE_YET

        elif not user.admin:
            request.setHeader('Status', '401 Unauthorized')
            return self.render_template('errors/error.html', request, {
                'title': 'Not Authorized',
                'message': 'You are not authorized to view this page'
            })

        return Resource.render(self, request)


class ModuleRoot(Resource):
    """
    The root entry point for a plugin's web interface.
    """

    def __init__(self, plugin, namespace, loader):
        super(ModuleRoot, self).__init__(
            plugin.application, plugin.make_environment(namespace, loader))
        self.namespace = namespace

    def blocks(self):
        return {}


class ErrorResource(Resource):

    def __init__(self, status, title, message, *args, **kwargs):
        super(ErrorResource, self).__init__(*args, **kwargs)
        self.status = status
        self.title = title
        self.message = message

    def render(self, request):
        if self.status:
            request.setHeader('Status', self.status)
        return self.render_template('core/errors/error.html', request, {
            'title': self.title,
            'message': self.message
        })


class NotFoundResource(ErrorResource):

    def __init__(self, *args, **kwargs):
        super(NotFoundResource, self).__init__('404 Not Found', 'Not Found',
                               'That page does not exist', *args, **kwargs)
