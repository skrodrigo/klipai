# Generated migration for SocialAccount and SocialPost models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('social_account_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('platform', models.CharField(choices=[('tiktok', 'TikTok'), ('instagram', 'Instagram'), ('youtube', 'YouTube'), ('facebook', 'Facebook'), ('linkedin', 'LinkedIn'), ('twitter', 'Twitter/X')], max_length=20)),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField(blank=True, null=True)),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('platform_user_id', models.CharField(max_length=255)),
                ('platform_username', models.CharField(max_length=255)),
                ('platform_display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('platform_profile_picture', models.URLField(blank=True, null=True)),
                ('permissions', models.JSONField(blank=True, default=list)),
                ('is_connected', models.BooleanField(default=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('connected_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'app_label': 'authentication',
            },
        ),
        migrations.CreateModel(
            name='SocialPost',
            fields=[
                ('social_post_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('caption', models.TextField()),
                ('media_urls', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('published', 'Published'), ('failed', 'Failed')], default='draft', max_length=20)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('platform_post_id', models.CharField(blank=True, max_length=255, null=True)),
                ('platform_post_url', models.URLField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('social_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='authentication.socialaccount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'app_label': 'authentication',
            },
        ),
        migrations.AddIndex(
            model_name='socialaccount',
            index=models.Index(fields=['user', 'platform'], name='authentication_user_id_platform_idx'),
        ),
        migrations.AddIndex(
            model_name='socialaccount',
            index=models.Index(fields=['platform', 'platform_user_id'], name='authentication_platform_user_id_idx'),
        ),
        migrations.AddConstraint(
            model_name='socialaccount',
            constraint=models.UniqueConstraint(fields=['user', 'platform', 'platform_user_id'], name='unique_social_account'),
        ),
        migrations.AddIndex(
            model_name='socialpost',
            index=models.Index(fields=['user', 'status'], name='authentication_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='socialpost',
            index=models.Index(fields=['social_account', 'status'], name='authentication_account_status_idx'),
        ),
    ]
