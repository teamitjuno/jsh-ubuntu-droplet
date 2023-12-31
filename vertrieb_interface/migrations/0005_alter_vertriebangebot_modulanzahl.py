# Generated by Django 4.2.2 on 2023-07-12 08:56

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vertrieb_interface", "0004_vertriebangebot_full_ticket_preis"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vertriebangebot",
            name="modulanzahl",
            field=models.PositiveIntegerField(
                default=0, validators=[django.core.validators.MinValueValidator(6)]
            ),
        ),
    ]
