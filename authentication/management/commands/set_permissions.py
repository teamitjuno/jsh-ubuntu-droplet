from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from authentication.models import User, Role


class Command(BaseCommand):
    help = "Set the necessary permissions for user and role"

    def handle(self, *args, **kwargs):
        user = User.objects.get(email="cw@juno-solar.com")
        permissions = Permission.objects.all()
        for perm in permissions:
            print(perm.codename)

        permission = Permission.objects.get(codename="change_user")
        user.user_permissions.add(permission)
        permission = Permission.objects.get(codename="can_change_user")
        user.user_permissions.add(permission)

        role = Role.objects.get(id=1)
        permission = Permission.objects.get(codename="change_user")
        role.permissions.add(permission)
        permission = Permission.objects.get(codename="can_change_user")
        role.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS("Permissions set successfully"))
