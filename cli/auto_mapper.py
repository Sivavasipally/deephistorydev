"""Automatic author-staff mapping based on email addresses."""

from datetime import datetime
from .models import AuthorStaffMapping, StaffDetails, Commit
from sqlalchemy import func


class AutoMapper:
    """Automatically map Git authors to staff members based on email."""

    def __init__(self, session):
        """Initialize AutoMapper.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def extract_email_domain(self, email):
        """Extract domain from email address.

        Args:
            email: Email address

        Returns:
            Domain part of email (e.g., 'company.com' from 'user@company.com')
        """
        if not email or '@' not in email:
            return None
        return email.split('@')[-1].lower()

    def normalize_email(self, email):
        """Normalize email address for comparison.

        Args:
            email: Email address

        Returns:
            Normalized email (lowercase, stripped)
        """
        if not email:
            return None
        return email.strip().lower()

    def extract_username_from_email(self, email):
        """Extract username part from email.

        Args:
            email: Email address (e.g., 'john.doe@company.com')

        Returns:
            Username part (e.g., 'john.doe')
        """
        if not email or '@' not in email:
            return None
        return email.split('@')[0].lower()

    def get_unmapped_authors(self):
        """Get list of Git authors not yet mapped to staff.

        Returns:
            List of dicts with author_name, author_email, commit_count
        """
        # Find all unique authors from commits
        authors_in_commits = self.session.query(
            Commit.author_name,
            Commit.author_email,
            func.count(Commit.id).label('commit_count')
        ).group_by(
            Commit.author_name,
            Commit.author_email
        ).all()

        # Find already mapped authors
        mapped_emails = set(
            email for (email,) in self.session.query(AuthorStaffMapping.author_email).all()
        )

        # Filter out mapped authors
        unmapped = []
        for author_name, author_email, commit_count in authors_in_commits:
            if author_email and author_email not in mapped_emails:
                unmapped.append({
                    'author_name': author_name,
                    'author_email': author_email,
                    'commit_count': commit_count
                })

        return unmapped

    def find_staff_by_email(self, author_email):
        """Find staff member by exact email match.

        Args:
            author_email: Author email from commits

        Returns:
            StaffDetails object or None
        """
        if not author_email:
            return None

        normalized_email = self.normalize_email(author_email)

        # Try exact match (case-insensitive)
        staff = self.session.query(StaffDetails).filter(
            func.lower(StaffDetails.email_address) == normalized_email
        ).first()

        return staff

    def find_staff_by_username_match(self, author_email, company_domains=None):
        """Find staff by matching username part of email.

        Useful when authors use different email domains (e.g., personal email vs company email).

        Args:
            author_email: Author email from commits
            company_domains: List of valid company email domains to consider

        Returns:
            StaffDetails object or None
        """
        if not author_email:
            return None

        username = self.extract_username_from_email(author_email)
        if not username:
            return None

        # Build query to find staff with matching username
        query = self.session.query(StaffDetails).filter(
            StaffDetails.email_address.isnot(None)
        )

        # If company domains specified, filter by domain
        if company_domains:
            domain_filters = []
            for domain in company_domains:
                domain_filters.append(
                    func.lower(StaffDetails.email_address).like(f'%@{domain.lower()}')
                )
            from sqlalchemy import or_
            query = query.filter(or_(*domain_filters))

        # Find staff where email username matches
        all_staff = query.all()
        for staff in all_staff:
            staff_username = self.extract_username_from_email(staff.email_address)
            if staff_username and staff_username == username:
                return staff

        return None

    def create_mapping(self, author_name, author_email, staff, mapping_method='auto_email', notes=''):
        """Create author-staff mapping.

        Args:
            author_name: Author name from commits
            author_email: Author email from commits
            staff: StaffDetails object
            mapping_method: Method used for mapping (e.g., 'auto_email', 'auto_username')
            notes: Optional notes

        Returns:
            AuthorStaffMapping object
        """
        # Check if mapping already exists
        existing = self.session.query(AuthorStaffMapping).filter_by(
            author_email=author_email
        ).first()

        if existing:
            # Update existing mapping
            existing.bank_id_1 = staff.bank_id_1
            existing.staff_id = staff.staff_id
            existing.staff_name = staff.staff_name
            existing.mapped_date = datetime.utcnow()
            existing.notes = f"{mapping_method}: {notes}".strip()
            self.session.commit()
            return existing
        else:
            # Create new mapping
            mapping = AuthorStaffMapping(
                author_name=author_name,
                author_email=author_email,
                bank_id_1=staff.bank_id_1,
                staff_id=staff.staff_id,
                staff_name=staff.staff_name,
                notes=f"{mapping_method}: {notes}".strip() if notes else mapping_method
            )
            self.session.add(mapping)
            self.session.commit()
            return mapping

    def auto_map_by_email(self, dry_run=False):
        """Automatically map authors to staff by exact email match.

        Args:
            dry_run: If True, only show what would be mapped without saving

        Returns:
            Dict with summary: {'matched': int, 'unmatched': int, 'mappings': list}
        """
        unmapped_authors = self.get_unmapped_authors()

        matched = []
        unmatched = []

        for author in unmapped_authors:
            staff = self.find_staff_by_email(author['author_email'])

            if staff:
                mapping_info = {
                    'author_name': author['author_name'],
                    'author_email': author['author_email'],
                    'staff_name': staff.staff_name,
                    'bank_id_1': staff.bank_id_1,
                    'commit_count': author['commit_count'],
                    'mapping_method': 'auto_email'
                }

                if not dry_run:
                    self.create_mapping(
                        author['author_name'],
                        author['author_email'],
                        staff,
                        mapping_method='auto_email',
                        notes='Automatic mapping by exact email match'
                    )

                matched.append(mapping_info)
            else:
                unmatched.append(author)

        return {
            'matched': len(matched),
            'unmatched': len(unmatched),
            'mappings': matched,
            'unmapped_authors': unmatched
        }

    def auto_map_by_username(self, company_domains, dry_run=False):
        """Automatically map authors to staff by username match.

        Useful when authors use different email domains.

        Args:
            company_domains: List of valid company email domains (e.g., ['company.com', 'company.org'])
            dry_run: If True, only show what would be mapped without saving

        Returns:
            Dict with summary: {'matched': int, 'unmatched': int, 'mappings': list}
        """
        unmapped_authors = self.get_unmapped_authors()

        matched = []
        unmatched = []

        for author in unmapped_authors:
            # Try exact email match first
            staff = self.find_staff_by_email(author['author_email'])

            # If no exact match, try username match
            if not staff:
                staff = self.find_staff_by_username_match(
                    author['author_email'],
                    company_domains=company_domains
                )

            if staff:
                mapping_method = 'auto_email' if self.normalize_email(author['author_email']) == self.normalize_email(staff.email_address) else 'auto_username'

                mapping_info = {
                    'author_name': author['author_name'],
                    'author_email': author['author_email'],
                    'staff_name': staff.staff_name,
                    'staff_email': staff.email_address,
                    'bank_id_1': staff.bank_id_1,
                    'commit_count': author['commit_count'],
                    'mapping_method': mapping_method
                }

                if not dry_run:
                    self.create_mapping(
                        author['author_name'],
                        author['author_email'],
                        staff,
                        mapping_method=mapping_method,
                        notes=f'Mapped: {author["author_email"]} -> {staff.email_address}'
                    )

                matched.append(mapping_info)
            else:
                unmatched.append(author)

        return {
            'matched': len(matched),
            'unmatched': len(unmatched),
            'mappings': matched,
            'unmapped_authors': unmatched
        }

    def auto_map_all(self, company_domains=None, dry_run=False):
        """Run all automatic mapping strategies.

        Args:
            company_domains: Optional list of company email domains for username matching
            dry_run: If True, only show what would be mapped without saving

        Returns:
            Dict with summary of all mappings
        """
        print("\n" + "=" * 80)
        print("AUTOMATIC AUTHOR-STAFF MAPPING")
        print("=" * 80)
        print(f"Mode: {'DRY RUN (no changes will be saved)' if dry_run else 'ACTIVE (mappings will be created)'}")
        print("=" * 80)

        # Strategy 1: Exact email match
        print("\n[INFO] Strategy 1: Exact Email Match")
        print("-" * 80)
        result_email = self.auto_map_by_email(dry_run=dry_run)
        print(f"   Matched: {result_email['matched']}")
        print(f"   Unmatched: {result_email['unmatched']}")

        # Strategy 2: Username match (if company domains provided)
        if company_domains:
            print(f"\n[INFO] Strategy 2: Username Match (domains: {', '.join(company_domains)})")
            print("-" * 80)
            result_username = self.auto_map_by_username(company_domains, dry_run=dry_run)
            print(f"   Matched: {result_username['matched']}")
            print(f"   Unmatched: {result_username['unmatched']}")
        else:
            result_username = {'matched': 0, 'unmatched': 0, 'mappings': [], 'unmapped_authors': []}

        # Combined summary
        total_matched = result_email['matched'] + result_username['matched']
        all_mappings = result_email['mappings'] + result_username['mappings']
        unmapped = result_username.get('unmapped_authors', result_email.get('unmapped_authors', []))

        print("\n" + "=" * 80)
        print("MAPPING SUMMARY")
        print("=" * 80)
        print(f"Total Matched: {total_matched}")
        print(f"Total Unmatched: {len(unmapped)}")
        print("=" * 80)

        if all_mappings:
            print("\n[SUCCESS] Matched Mappings:")
            print("-" * 80)
            for mapping in all_mappings[:10]:  # Show first 10
                print(f"   {mapping['author_name']} <{mapping['author_email']}>")
                print(f"   -> {mapping['staff_name']} ({mapping['bank_id_1']}) - {mapping['commit_count']} commits")
                print(f"      Method: {mapping['mapping_method']}")
                print()
            if len(all_mappings) > 10:
                print(f"   ... and {len(all_mappings) - 10} more mappings")

        if unmapped:
            print("\n[WARNING] Unmapped Authors (require manual mapping):")
            print("-" * 80)
            for author in unmapped[:10]:  # Show first 10
                print(f"   {author['author_name']} <{author['author_email']}> - {author['commit_count']} commits")
            if len(unmapped) > 10:
                print(f"   ... and {len(unmapped) - 10} more unmapped authors")

        if dry_run:
            print("\n[INFO] DRY RUN MODE - No changes were saved to database")
            print("       Run again without --dry-run to save mappings")

        return {
            'total_matched': total_matched,
            'total_unmatched': len(unmapped),
            'all_mappings': all_mappings,
            'unmapped_authors': unmapped,
            'by_email': result_email,
            'by_username': result_username
        }
