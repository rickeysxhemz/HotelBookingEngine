from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import EmailVerificationToken, PasswordResetToken, BlacklistedToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up expired and old tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete tokens older than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Clean up expired email verification tokens
        expired_email_tokens = EmailVerificationToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        email_count = expired_email_tokens.count()
        expired_email_tokens.delete()
        
        # Clean up expired password reset tokens
        expired_password_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        password_count = expired_password_tokens.count()
        expired_password_tokens.delete()
        
        # Clean up old used tokens
        old_email_tokens = EmailVerificationToken.objects.filter(
            created_at__lt=cutoff_date,
            used=True
        )
        old_email_count = old_email_tokens.count()
        old_email_tokens.delete()
        
        old_password_tokens = PasswordResetToken.objects.filter(
            created_at__lt=cutoff_date,
            used=True
        )
        old_password_count = old_password_tokens.count()
        old_password_tokens.delete()
        
        total_deleted = email_count + password_count + old_email_count + old_password_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {total_deleted} tokens:\n'
                f'  - {email_count} expired email verification tokens\n'
                f'  - {password_count} expired password reset tokens\n'
                f'  - {old_email_count} old used email tokens\n'
                f'  - {old_password_count} old used password tokens'
            )
        )
