# Generated by Django 5.0.2 on 2025-03-17 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0028_user_salutation_alter_user_typ"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="smtp_body",
            field=models.TextField(blank=True, default="", null=True),
        ),
    ]
