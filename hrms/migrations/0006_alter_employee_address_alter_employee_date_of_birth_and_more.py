# Generated by Django 4.2.4 on 2024-01-04 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('hrms', '0005_alter_employee_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='department',
            field=models.CharField(default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='designation',
            field=models.CharField(default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='full_name',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='employee_groups', to='auth.group'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='image',
            field=models.ImageField(default='', upload_to='media/employee_images'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='salary',
            field=models.CharField(default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, related_name='employee_user_permissions', to='auth.permission'),
        ),
    ]
