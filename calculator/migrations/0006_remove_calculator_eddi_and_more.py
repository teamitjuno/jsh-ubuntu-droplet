# Generated by Django 5.0.2 on 2024-08-14 07:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("calculator", "0005_remove_calculator_elwa_typ_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="calculator",
            name="eddi",
        ),
        migrations.RemoveField(
            model_name="calculator",
            name="eddi_angebot_price",
        ),
    ]
