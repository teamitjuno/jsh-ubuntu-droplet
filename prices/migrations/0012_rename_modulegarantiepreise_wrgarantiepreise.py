# Generated by Django 5.0.2 on 2024-07-01 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0011_solarmodulepreise_datenblatt"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ModuleGarantiePreise",
            new_name="WrGarantiePreise",
        ),
    ]