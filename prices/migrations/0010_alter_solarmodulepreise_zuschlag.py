# Generated by Django 5.0.2 on 2024-06-05 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0009_solarmodulepreise_zuschlag"),
    ]

    operations = [
        migrations.AlterField(
            model_name="solarmodulepreise",
            name="zuschlag",
            field=models.DecimalField(decimal_places=3, default=1.0, max_digits=10),
        ),
    ]
