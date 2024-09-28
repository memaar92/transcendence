# Generated by Django 5.0.6 on 2024-09-28 13:59

import django.db.models.deletion
import utils.utils
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('displayname', models.CharField(max_length=20, unique=True)),
                ('profile_picture', models.ImageField(default='mediafiles/default.png', upload_to=utils.utils.random_filename)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_42_auth', models.BooleanField(default=False)),
                ('email_verified', models.BooleanField(default=False)),
                ('totp_secret', models.CharField(blank=True, max_length=32, null=True)),
                ('is_2fa_enabled', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Games',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('visitor_score', models.IntegerField()),
                ('home_score', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('home_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='home_games', to=settings.AUTH_USER_MODEL)),
                ('visitor_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='visitor_games', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
