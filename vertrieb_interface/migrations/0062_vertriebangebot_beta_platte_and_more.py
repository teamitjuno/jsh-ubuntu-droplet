# Generated by Django 5.0.2 on 2024-08-26 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vertrieb_interface", "0061_vertriebangebot_dachhakenkunde_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vertriebangebot",
            name="beta_platte",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vertriebangebot",
            name="metall_ziegel",
            field=models.BooleanField(default=False),
        ),
    ]