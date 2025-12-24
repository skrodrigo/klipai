import uuid
from django.db import models
from .user import CustomUser


class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter/X'),
    ]

    social_account_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # OAuth credentials
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Account info
    platform_user_id = models.CharField(max_length=255)
    platform_username = models.CharField(max_length=255)
    platform_display_name = models.CharField(max_length=255, null=True, blank=True)
    platform_profile_picture = models.URLField(null=True, blank=True)
    
    # Permissions
    permissions = models.JSONField(default=list, blank=True)
    
    # Status
    is_connected = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'authentication'
        unique_together = ('user', 'platform', 'platform_user_id')
        indexes = [
            models.Index(fields=['user', 'platform']),
            models.Index(fields=['platform', 'platform_user_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.platform} ({self.platform_username})"
    
    def is_token_expired(self):
        from django.utils import timezone
        if self.token_expires_at:
            return timezone.now() >= self.token_expires_at
        return False


class SocialPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]

    social_post_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='social_posts')
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='posts')
    
    # Content
    caption = models.TextField()
    media_urls = models.JSONField(default=list, blank=True)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Platform response
    platform_post_id = models.CharField(max_length=255, null=True, blank=True)
    platform_post_url = models.URLField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'authentication'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['social_account', 'status']),
        ]
    
    def __str__(self):
        return f"Post to {self.social_account.platform} - {self.status}"
