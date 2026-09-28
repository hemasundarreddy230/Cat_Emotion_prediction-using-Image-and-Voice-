from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Set up a demo Google OAuth Social Application'

    def handle(self, *args, **options):
        # Get or create the default site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'CatCare AI Local'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created site: {site.domain}')
            )
        else:
            # Update existing site
            site.domain = 'localhost:8000'
            site.name = 'CatCare AI Local'
            site.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated site: {site.domain}')
            )

        # Create or update Google Social Application
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth Demo',
                'client_id': 'demo-client-id-replace-with-real',
                'secret': 'demo-secret-replace-with-real',
            }
        )
        
        # Add the site to the social app
        google_app.sites.add(site)
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Google Social Application (Demo)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Google Social Application already exists')
            )
        
        self.stdout.write(
            self.style.WARNING('\n' + '='*60)
        )
        self.stdout.write(
            self.style.WARNING('IMPORTANT: This is a DEMO setup!')
        )
        self.stdout.write(
            self.style.WARNING('To enable real Google Sign-In:')
        )
        self.stdout.write(
            self.style.WARNING('1. Get Google OAuth credentials from Google Cloud Console')
        )
        self.stdout.write(
            self.style.WARNING('2. Go to Django Admin: http://localhost:8000/admin/')
        )
        self.stdout.write(
            self.style.WARNING('3. Update the Google Social Application with real credentials')
        )
        self.stdout.write(
            self.style.WARNING('4. See GOOGLE_OAUTH_SETUP_GUIDE.md for detailed instructions')
        )
        self.stdout.write(
            self.style.WARNING('='*60)
        )