# Django related imports
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Local imports from 'authentication'
from authentication.models import User


def vertrieb_check(user):
    return User.objects.filter(id=user.id, beruf="Vertrieb").exists()


class VertriebCheckMixin(UserPassesTestMixin):
    def test_func(self):
        return vertrieb_check(self.request.user)
