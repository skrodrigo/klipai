import secrets
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from authentication.services.oauth_service import OAuthManager
from authentication.models import SocialAccount
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def oauth_authorize(request, platform):
    """
    Initiate OAuth flow for a social platform
    Returns authorization URL and state for CSRF protection
    """
    try:
        provider = OAuthManager.get_provider(platform)
        state = secrets.token_urlsafe(32)
        
        # Store state in session for verification
        request.session[f'oauth_state_{platform}'] = state
        request.session.save()
        
        auth_url = provider.get_authorization_url(state)
        
        return Response({
            'authorization_url': auth_url,
            'state': state,
        }, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"OAuth authorize error: {str(e)}")
        return Response({
            'error': 'Failed to initiate OAuth flow'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@csrf_exempt
def oauth_callback(request, platform):
    """
    OAuth callback handler for all platforms
    Exchanges authorization code for access token
    """
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            return JsonResponse({
                'error': f'OAuth error: {error}',
                'error_description': request.GET.get('error_description', '')
            }, status=400)
        
        if not code or not state:
            return JsonResponse({
                'error': 'Missing code or state parameter'
            }, status=400)
        
        # Verify state from session
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({
                'error': 'Missing user_id parameter'
            }, status=400)
        
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'error': 'User not found'
            }, status=404)
        
        # Handle OAuth callback
        social_account = OAuthManager.handle_oauth_callback(user, platform, code, state)
        
        # Redirect to frontend with success
        frontend_url = f"{request.scheme}://{request.get_host()}"
        redirect_url = f"{frontend_url}/dashboard/accounts?platform={platform}&connected=true&account={social_account.platform_username}"
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully connected {platform} account',
            'redirect_url': redirect_url,
            'social_account': {
                'platform': social_account.platform,
                'username': social_account.platform_username,
                'display_name': social_account.platform_display_name,
                'profile_picture': social_account.platform_profile_picture,
            }
        })
    
    except Exception as e:
        logger.error(f"OAuth callback error for {platform}: {str(e)}")
        return JsonResponse({
            'error': 'Failed to process OAuth callback',
            'details': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_social_accounts(request):
    """
    List all connected social accounts for the user
    """
    try:
        social_accounts = SocialAccount.objects.filter(user=request.user, is_connected=True)
        
        accounts_data = []
        for account in social_accounts:
            accounts_data.append({
                'social_account_id': str(account.social_account_id),
                'platform': account.platform,
                'username': account.platform_username,
                'display_name': account.platform_display_name,
                'profile_picture': account.platform_profile_picture,
                'connected_at': account.connected_at.isoformat(),
                'last_used_at': account.last_used_at.isoformat() if account.last_used_at else None,
                'token_expired': account.is_token_expired(),
            })
        
        return Response({
            'accounts': accounts_data,
            'total': len(accounts_data)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"List social accounts error: {str(e)}")
        return Response({
            'error': 'Failed to list social accounts'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_social_account(request, platform):
    """
    Disconnect a social account
    """
    try:
        social_account = SocialAccount.objects.get(
            user=request.user,
            platform=platform,
            is_connected=True
        )
        
        OAuthManager.disconnect_account(social_account)
        
        return Response({
            'success': True,
            'message': f'Successfully disconnected {platform} account'
        }, status=status.HTTP_200_OK)
    
    except SocialAccount.DoesNotExist:
        return Response({
            'error': f'No connected {platform} account found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Disconnect account error: {str(e)}")
        return Response({
            'error': 'Failed to disconnect account'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_social_token(request, platform):
    """
    Refresh access token for a social account
    """
    try:
        social_account = SocialAccount.objects.get(
            user=request.user,
            platform=platform,
            is_connected=True
        )
        
        if not social_account.refresh_token:
            return Response({
                'error': f'{platform} account does not support token refresh'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        provider = OAuthManager.get_provider(platform)
        token_data = provider.refresh_access_token(social_account.refresh_token)
        
        # Update access token
        social_account.access_token = token_data['access_token']
        if 'refresh_token' in token_data:
            social_account.refresh_token = token_data['refresh_token']
        if 'expires_in' in token_data:
            from django.utils import timezone
            from datetime import timedelta
            social_account.token_expires_at = timezone.now() + timedelta(seconds=token_data['expires_in'])
        social_account.save()
        
        return Response({
            'success': True,
            'message': f'Successfully refreshed {platform} token'
        }, status=status.HTTP_200_OK)
    
    except SocialAccount.DoesNotExist:
        return Response({
            'error': f'No connected {platform} account found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        return Response({
            'error': 'Failed to refresh token'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
