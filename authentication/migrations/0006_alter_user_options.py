# Generated by Django 4.2.2 on 2023-08-28 08:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0005_alter_user_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name_plural": "Users"},
        ),
    ]
