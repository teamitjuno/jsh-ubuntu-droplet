# Generated by Django 4.2.2 on 2023-08-09 22:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projektant_interface", "0004_alter_project_wechselrichter1"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="bauplan_img",
            field=models.ImageField(blank=True, null=True, upload_to=""),
        ),
        migrations.AddField(
            model_name="project",
            name="bauplan_pdf",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]