# Generated by Django 5.0.2 on 2024-08-21 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0059_vertriebangebot_genehmigung_rabatt_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="apzFeld",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vertriebangebot",
            name="midZaehler",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="vertriebangebot",
            name="potenzialausgleich",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vertriebangebot",
            name="zaehlerschrank",
            field=models.BooleanField(default=False),
        ),
    ]