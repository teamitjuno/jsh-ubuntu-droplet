# Generated by Django 5.0.2 on 2024-08-21 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "vertrieb_interface",
            "0060_vertriebangebot_apzfeld_vertriebangebot_midzaehler_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="dachhakenKunde",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vertriebangebot",
            name="geruestKunde",
            field=models.BooleanField(default=False),
        ),
    ]