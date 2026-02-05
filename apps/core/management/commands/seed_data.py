"""Seed database with sample B2B data for development."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.organizations.models import Membership, MembershipRole, Organization, Team

User = get_user_model()


class Command(BaseCommand):
    """Seed database with sample B2B data for development."""

    help = "Seed database with sample organizations, teams, and users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )
        parser.add_argument(
            "--orgs",
            type=int,
            default=2,
            help="Number of organizations to create (default: 2)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Membership.objects.all().delete()
            Team.objects.all().delete()
            Organization.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing data"))

        admin = self.create_admin_user()
        users = self.create_sample_users()
        self.create_organizations_with_teams(admin, users, options["orgs"])
        self.stdout.write(self.style.SUCCESS("\nSeeding complete!"))
        self.print_summary()

    def create_admin_user(self):
        """Create an admin user if it doesn't exist."""
        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User",
                "is_superuser": True,
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin@example.com"))
        else:
            self.stdout.write("Admin user already exists")
        return admin

    def create_sample_users(self):
        """Create sample users for organizations."""
        users = []
        user_data = [
            ("alice", "Alice", "Johnson", "alice@example.com"),
            ("bob", "Bob", "Smith", "bob@example.com"),
            ("charlie", "Charlie", "Brown", "charlie@example.com"),
            ("diana", "Diana", "Garcia", "diana@example.com"),
            ("evan", "Evan", "Williams", "evan@example.com"),
            ("fiona", "Fiona", "Davis", "fiona@example.com"),
        ]

        for username, first, last, email in user_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "first_name": first,
                    "last_name": last,
                },
            )
            if created:
                user.set_password("password123")
                user.save()
                self.stdout.write(f"Created user: {email}")
            users.append(user)

        return users

    def create_organizations_with_teams(self, admin, users, num_orgs: int):
        """Create organizations with teams and members."""
        org_data = [
            {
                "name": "Acme Corporation",
                "description": "A leading technology company specializing in innovative solutions.",
                "plan": "pro",
                "teams": ["Engineering", "Product", "Marketing"],
            },
            {
                "name": "Startup Labs",
                "description": "Fast-moving startup building the future of work.",
                "plan": "free",
                "teams": ["Development", "Design"],
            },
            {
                "name": "Enterprise Inc",
                "description": "Global enterprise solutions provider.",
                "plan": "enterprise",
                "teams": ["Engineering", "Sales", "Support", "HR"],
            },
        ]

        for i, data in enumerate(org_data[:num_orgs]):
            org, created = Organization.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "plan": data["plan"],
                    "settings": {"allow_invitations": True, "require_2fa": False},
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created organization: {org.name}"))

                # Add admin as owner
                Membership.objects.create(
                    user=admin,
                    organization=org,
                    role=MembershipRole.OWNER,
                    job_title="CEO",
                    department="Executive",
                )

                # Create teams
                teams = []
                for team_name in data["teams"]:
                    team, _ = Team.objects.get_or_create(
                        organization=org,
                        slug=slugify(team_name),
                        defaults={
                            "name": team_name,
                            "description": f"The {team_name} team at {org.name}",
                        },
                    )
                    teams.append(team)
                    self.stdout.write(f"  Created team: {team_name}")

                # Assign users to organization with different roles
                roles = [MembershipRole.ADMIN, MembershipRole.MEMBER, MembershipRole.VIEWER]
                start_idx = i * 2
                org_users = users[start_idx : start_idx + 3] if start_idx < len(users) else users[:3]

                for j, user in enumerate(org_users):
                    role = roles[j % len(roles)]
                    membership = Membership.objects.create(
                        user=user,
                        organization=org,
                        role=role,
                        job_title=self._get_job_title(role),
                        department=teams[0].name if teams else "General",
                    )
                    # Add to first team
                    if teams:
                        membership.teams.add(teams[0])
                    self.stdout.write(f"  Added {user.email} as {role}")
            else:
                self.stdout.write(f"Organization {org.name} already exists")

    def _get_job_title(self, role: str) -> str:
        """Get a job title based on role."""
        titles = {
            MembershipRole.OWNER: "Founder",
            MembershipRole.ADMIN: "Team Lead",
            MembershipRole.MEMBER: "Engineer",
            MembershipRole.VIEWER: "Analyst",
        }
        return titles.get(role, "Employee")

    def print_summary(self):
        """Print a summary of created data."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SEED DATA SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Organizations: {Organization.objects.count()}")
        self.stdout.write(f"Teams: {Team.objects.count()}")
        self.stdout.write(f"Memberships: {Membership.objects.count()}")
        self.stdout.write("\nTest Credentials:")
        self.stdout.write("  Admin: admin@example.com / admin123")
        self.stdout.write("  Users: alice@example.com / password123")
        self.stdout.write("         bob@example.com / password123")
        self.stdout.write("         charlie@example.com / password123")
        self.stdout.write("=" * 50)
