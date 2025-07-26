# Django imports
from django.core.management.base import BaseCommand
from django.utils import timezone

# Local imports
from accounts.services import TokenBlacklistService


class Command(BaseCommand):
    help = 'Clean up expired blacklisted tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=20,
            help='Remove tokens older than this many days (default: 20)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days_old = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Cleaning up blacklisted tokens older than {days_old} days...')
        
        if dry_run:
            from accounts.models import BlacklistedToken
            cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
            count = BlacklistedToken.objects.filter(blacklisted_at__lt=cutoff_date).count()
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} blacklisted tokens')
            )
        else:
            deleted_count = TokenBlacklistService.cleanup_expired_tokens(days_old)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} expired blacklisted tokens')
            )
