# Generated by Django 4.2.5 on 2023-11-28 11:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0010_user_is_home_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="initial_text_for_email",
            field=models.TextField(blank=True, null=True),
        ),
    ]
