# Generated by Django 5.0.2 on 2024-08-28 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0065_vertriebangebot_anzahlung_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="finanzierung",
            field=models.BooleanField(default=False),
        ),
    ]
