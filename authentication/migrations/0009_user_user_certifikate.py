# Generated by Django 4.2.5 on 2023-10-04 12:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "authentication",
            "0008_user_initial_anzoptimizer_user_initial_anz_speicher_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="user_certifikate",
            field=models.ImageField(
                blank=True, null=True, upload_to="assets/images/users/certifikates/"
            ),
        ),
    ]