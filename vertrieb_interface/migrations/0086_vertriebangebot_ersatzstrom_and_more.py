# Generated by Django 5.0.2 on 2025-02-07 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0085_remove_vertriebangebot_gesamtkapazitat"),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="ersatzstrom",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vertriebticket",
            name="ersatzstrom",
            field=models.BooleanField(default=False),
        ),
    ]
