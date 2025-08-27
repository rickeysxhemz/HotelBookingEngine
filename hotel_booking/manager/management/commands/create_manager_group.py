from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create Manager group and assign manager permissions'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Manager')

        # Define required permissions by (app_label, model, actions)
        perms_map = {
            'bookings': {
                'booking': ['add', 'change', 'delete', 'view'],
                'bookingextra': ['add', 'change', 'delete', 'view'],
                'bookingguest': ['add', 'change', 'delete', 'view'],
                'bookinghistory': ['add', 'change', 'delete', 'view'],
            },
            'core': {
                'extra': ['add', 'change', 'delete', 'view'],
                'hotel': ['add', 'change', 'delete', 'view'],
                'room': ['add', 'change', 'delete', 'view'],
                'roomamenity': ['add', 'change', 'delete', 'view'],
                'roomimage': ['add', 'change', 'delete', 'view'],
                'roomtype': ['add', 'change', 'delete', 'view'],
                'roomtypeamenity': ['add', 'change', 'delete', 'view'],
                'seasonalpricing': ['add', 'change', 'delete', 'view'],
            }
        }

        added = []
        missing = []

        for app_label, models in perms_map.items():
            for model, actions in models.items():
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model)
                except ContentType.DoesNotExist:
                    missing.append(f'{app_label}.{model}')
                    continue

                for action in actions:
                    codename = f'{action}_{model}'
                    try:
                        perm = Permission.objects.get(content_type=ct, codename=codename)
                        group.permissions.add(perm)
                        added.append(f'{app_label}.{codename}')
                    except Permission.DoesNotExist:
                        missing.append(f'{app_label}.{codename}')

        self.stdout.write(self.style.SUCCESS(f'Created/updated group "Manager"'))
        if added:
            self.stdout.write(self.style.SUCCESS(f'Added permissions: {added}'))
        if missing:
            self.stdout.write(self.style.WARNING(f'Missing content types or permissions: {missing}'))
