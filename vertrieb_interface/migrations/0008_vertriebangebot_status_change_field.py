# Generated by Django 4.2.2 on 2023-07-13 22:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vertrieb_interface", "0007_alter_vertriebangebot_arbeitspreis_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="status_change_field",
            field=models.DateField(blank=True, null=True),
        ),
    ]
