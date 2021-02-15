from django.contrib.auth.backends import ModelBackend

class AuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super(AuthBackend, self).authenticate(request, username, password, **kwargs)
        if user and user.profile.:
            return user
        return None