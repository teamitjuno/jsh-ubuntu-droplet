# Generated by Django 5.0.2 on 2024-06-05 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0008_remove_elektrikpreis_actual_price_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="solarmodulepreise",
            name="zuschlag",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=10),
        ),
    ]
