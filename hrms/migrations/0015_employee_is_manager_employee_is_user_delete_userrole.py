# Generated by Django 4.2.4 on 2024-01-05 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hrms', '0014_rename_userprofile_userrole'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='is_manager',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employee',
            name='is_user',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='UserRole',
        ),
    ]
