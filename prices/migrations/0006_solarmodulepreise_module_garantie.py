# Generated by Django 5.0.2 on 2024-03-26 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0005_alter_anderekonfigurationwerte_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="solarmodulepreise",
            name="module_garantie",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]