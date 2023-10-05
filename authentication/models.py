import os
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone
from authentication.constants import DEFAULT_ROLES
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import (
    make_password,
)


class CustomUserManager(UserManager):
    """custom user manager"""

    def _create_user(self, email, password=None, **extra_fields):
        if email is None:
            raise ValueError("Email field is required.")
        if password is None:
            raise ValueError("Password field is required.")

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        role_id = DEFAULT_ROLES["admin"]
        role_name = "admin"
        extra_fields["role"] = get_or_create_role(role_id, role_name)

        return self._create_user(
            username=email, email=email, password=password, **extra_fields
        )


class Role(models.Model):
    """user's Role which is used for giving permissions"""

    name = models.CharField(max_length=50)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name


def get_or_create_role(role_id, role_name):
    role, created = Role.objects.get_or_create(id=role_id, defaults={"name": role_name})
    return role


class User(AbstractBaseUser, PermissionsMixin, models.Model):
    """This is my custom User model"""

    zoho_id = models.PositiveBigIntegerField(unique=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(_("password"), max_length=128)
    username = models.CharField(unique=True, max_length=100, null=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    age = models.PositiveSmallIntegerField(null=True, default=2)
    phone = models.CharField(
        ("phone"), max_length=15, unique=True, null=True, blank=True
    )
    avatar = models.ImageField(upload_to="assets/images/users/", null=True, blank=True)
    user_certifikate = models.ImageField(
        upload_to="assets/images/users/certifikates/", null=True, blank=True
    )
    is_staff = models.BooleanField(default=False)
    beruf = models.CharField(
        max_length=30,
        choices=[
            ("Elektriker", "Elektriker"),
            ("Vertrieb", "Vertrieb"),
            ("Projektant", "Projektant"),
        ],
        null=True,
        default=None,
    )
    users_aufschlag = models.PositiveSmallIntegerField(null=False, default=0)
    typ = models.CharField(
        max_length=255,
        choices=[
            ("keine", "keine"),
            ("Evolti", "Evolti"),
            ("Vertrieb", "Vertrieb"),
            ("Freelancer", "Freelancer"),
        ],
        null=True,
        default=None,
    )
    kuerzel = models.CharField(max_length=3, null=True, unique=True)
    gerat = models.CharField(max_length=30, null=True, blank=True, unique=False)
    is_active = models.BooleanField(default=True)
    imei = models.BigIntegerField(null=True, blank=True, unique=True)
    anbieter = models.CharField(max_length=30, null=True, blank=True, unique=False)
    google_account = models.EmailField(null=True, blank=True, unique=True)
    google_passwort = models.CharField(
        max_length=30, null=True, blank=True, unique=False
    )
    sim_pin = models.SmallIntegerField(null=True, blank=True, unique=False)
    is_superuser = models.BooleanField(default=False)
    zoho_data = models.JSONField(default=dict, blank=True)
    zoho_data_text = models.TextField(default="", blank=True)
    sonstiges = models.TextField(blank=True, null=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
    )

    smtp_server = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=False,
        default=os.getenv("EMAIL_HOST"),
    )
    smtp_port = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        unique=False,
        default=os.getenv("EMAIL_PORT"),
    )
    smtp_username = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        unique=False,
        default=os.getenv("EMAIL_HOST_USER"),
    )
    smtp_password = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        unique=False,
        default=os.getenv("EMAIL_HOST_PASSWORD"),
    )
    smtp_subject = models.TextField(
        blank=True, null=True, default="Juno-Solar Dokument-Anlage"
    )
    smtp_body = models.TextField(
        blank=True,
        null=True,
        default="""Sehr geehrter Kunde, in diesem Schreiben finden Sie die beigefügten PDF-Dokumente.

                                                                    Mit freundlichen Grüßen, Juno-Solar""",
    )

    top_verkaufer_container_view = models.BooleanField(default=True)
    profile_container_view = models.BooleanField(default=True)
    activity_container_view = models.BooleanField(default=True)
    angebot_statusubersicht_view = models.BooleanField(default=True)
    pv_rechner_view = models.BooleanField(default=True)
    anzahl_sol_module_view = models.BooleanField(default=True)

    MAP_NOTIZEN_CHOICES = [
        ("Map", "Map"),
        ("Notizen", "Notizen"),
    ]
    map_notizen_container_view = models.CharField(
        choices=MAP_NOTIZEN_CHOICES, default="Map"
    )

    initial_verbrauch = models.FloatField(
        default=15000, validators=[MinValueValidator(0)]  # type: ignore
    )
    initial_grundpreis = models.FloatField(
        default=9.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    initial_arbeitspreis = models.FloatField(
        default=46.8, validators=[MinValueValidator(0)]  # type: ignore
    )
    initial_prognose = models.FloatField(
        default=5.2, validators=[MinValueValidator(0)]  # type: ignore
    )
    initial_zeitraum = models.PositiveIntegerField(default=15)
    initial_bis10kWp = models.FloatField(
        default=8.20, validators=[MinValueValidator(0)]  # type: ignore
    )
    initial_bis40kWp = models.FloatField(
        default=7.10, validators=[MinValueValidator(0)]  # type: ignore
    )

    initial_anz_speicher = models.PositiveIntegerField(default=0)
    initial_wandhalterung_fuer_speicher = models.BooleanField(default=False)

    initial_ausrichtung = models.CharField(max_length=10, default="Ost/West")
    initial_komplex = models.CharField(max_length=30, default="sehr komplex")

    initial_solar_module = models.CharField(
        max_length=100,
        default="Phono Solar PS420M7GFH-18/VNH",
    )
    initial_modulanzahl = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    initial_garantieWR = models.CharField(max_length=10, default="10 Jahre")
    initial_elwa = models.BooleanField(default=False)
    initial_thor = models.BooleanField(default=False)
    initial_heizstab = models.BooleanField(default=False)
    initial_notstrom = models.BooleanField(default=False)
    initial_anzOptimizer = models.PositiveIntegerField(default=0)

    initial_wallboxtyp = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    initial_wallbox_anzahl = models.PositiveIntegerField(default=0)
    intial_kabelanschluss = models.FloatField(
        default=10.0, validators=[MinValueValidator(0)], blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date_joined = models.DateTimeField(("date joined"), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = "email"

    USERNAME_FIELD = EMAIL_FIELD
    REQUIRED_FIELDS = []

    class Meta:
        # db_table = "users"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    def get_short_name(self):
        return self.first_name

    def save(self, *args, **kwargs):
        self.smtp_server = "send.one.com"

        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password

    @receiver(post_migrate)
    def create_default_roles(sender, **kwargs):
        # Create or get default roles
        for role_name, role_id in DEFAULT_ROLES.items():
            get_or_create_role(role_id, role_name)

        # Assign all permissions to admin role
        try:
            admin_role = Role.objects.get(name="admin")
            all_permissions = Permission.objects.all()
            admin_role.permissions.set(all_permissions)
        except Role.DoesNotExist:
            pass
