"""Streamlit dashboard for Git history analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func, desc
from datetime import datetime

from config import Config
from models import (
    get_engine, get_session, init_database,
    Repository, Commit, PullRequest, PRApproval, StaffDetails, AuthorStaffMapping
)


class GitHistoryDashboard:
    """Dashboard for visualizing Git history data."""

    def __init__(self):
        """Initialize dashboard."""
        self.config = Config()
        self.db_config = self.config.get_db_config()
        self.engine = get_engine(self.db_config)

    def get_top_commits_by_lines(self, limit=10):
        """Get top commits by lines changed.

        Args:
            limit: Number of top commits to return

        Returns:
            DataFrame with top commits
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                Commit.commit_hash,
                Commit.author_name,
                Commit.author_email,
                Commit.commit_date,
                Commit.message,
                Commit.lines_added,
                Commit.lines_deleted,
                (Commit.lines_added + Commit.lines_deleted).label('total_lines'),
                Commit.files_changed,
                Repository.project_key,
                Repository.slug_name
            ).join(
                Repository, Commit.repository_id == Repository.id
            ).order_by(
                desc('total_lines')
            ).limit(limit)

            results = query.all()

            data = [{
                'Commit Hash': r.commit_hash[:8],
                'Full Hash': r.commit_hash,
                'Author': r.author_name,
                'Email': r.author_email,
                'Date': r.commit_date,
                'Message': r.message[:100] + '...' if len(r.message) > 100 else r.message,
                'Lines Added': r.lines_added,
                'Lines Deleted': r.lines_deleted,
                'Total Lines': r.total_lines,
                'Files Changed': r.files_changed,
                'Repository': f"{r.project_key}/{r.slug_name}"
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_top_pr_approvers(self, limit=10):
        """Get top PR approvers.

        Args:
            limit: Number of top approvers to return

        Returns:
            DataFrame with top approvers
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                PRApproval.approver_name,
                PRApproval.approver_email,
                func.count(PRApproval.id).label('approvals_count'),
                func.count(func.distinct(PullRequest.repository_id)).label('repositories_count')
            ).join(
                PullRequest, PRApproval.pull_request_id == PullRequest.id
            ).group_by(
                PRApproval.approver_name,
                PRApproval.approver_email
            ).order_by(
                desc('approvals_count')
            ).limit(limit)

            results = query.all()

            data = [{
                'Approver Name': r.approver_name,
                'Email': r.approver_email,
                'Total Approvals': r.approvals_count,
                'Repositories': r.repositories_count
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_all_commits(self):
        """Get all commits for detailed view.

        Returns:
            DataFrame with all commits
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                Commit.commit_hash,
                Commit.author_name,
                Commit.author_email,
                Commit.committer_name,
                Commit.commit_date,
                Commit.message,
                Commit.lines_added,
                Commit.lines_deleted,
                (Commit.lines_added + Commit.lines_deleted).label('total_lines'),
                Commit.files_changed,
                Commit.branch,
                Repository.project_key,
                Repository.slug_name
            ).join(
                Repository, Commit.repository_id == Repository.id
            ).order_by(
                desc(Commit.commit_date)
            )

            results = query.all()

            data = [{
                'Commit Hash': r.commit_hash[:8],
                'Full Hash': r.commit_hash,
                'Author': r.author_name,
                'Author Email': r.author_email,
                'Committer': r.committer_name,
                'Date': r.commit_date,
                'Message': r.message,
                'Lines Added': r.lines_added,
                'Lines Deleted': r.lines_deleted,
                'Total Lines': r.total_lines,
                'Files Changed': r.files_changed,
                'Branch': r.branch,
                'Project': r.project_key,
                'Repository': r.slug_name,
                'Full Repo Name': f"{r.project_key}/{r.slug_name}"
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_all_pull_requests(self):
        """Get all pull requests for detailed view.

        Returns:
            DataFrame with all pull requests
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                PullRequest.pr_number,
                PullRequest.title,
                PullRequest.description,
                PullRequest.author_name,
                PullRequest.author_email,
                PullRequest.created_date,
                PullRequest.merged_date,
                PullRequest.state,
                PullRequest.source_branch,
                PullRequest.target_branch,
                PullRequest.lines_added,
                PullRequest.lines_deleted,
                (PullRequest.lines_added + PullRequest.lines_deleted).label('total_lines'),
                PullRequest.commits_count,
                func.count(PRApproval.id).label('approvals_count'),
                Repository.project_key,
                Repository.slug_name
            ).join(
                Repository, PullRequest.repository_id == Repository.id
            ).outerjoin(
                PRApproval, PullRequest.id == PRApproval.pull_request_id
            ).group_by(
                PullRequest.id
            ).order_by(
                desc(PullRequest.created_date)
            )

            results = query.all()

            data = [{
                'PR Number': r.pr_number,
                'Title': r.title,
                'Description': r.description[:200] + '...' if len(r.description) > 200 else r.description,
                'Author': r.author_name,
                'Author Email': r.author_email,
                'Created Date': r.created_date,
                'Merged Date': r.merged_date,
                'State': r.state,
                'Source Branch': r.source_branch,
                'Target Branch': r.target_branch,
                'Lines Added': r.lines_added,
                'Lines Deleted': r.lines_deleted,
                'Total Lines': r.total_lines,
                'Commits': r.commits_count,
                'Approvals': r.approvals_count,
                'Project': r.project_key,
                'Repository': r.slug_name,
                'Full Repo Name': f"{r.project_key}/{r.slug_name}"
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_commit_stats(self):
        """Get overall commit statistics.

        Returns:
            Dictionary with statistics
        """
        session = get_session(self.engine)
        try:
            total_commits = session.query(func.count(Commit.id)).scalar()
            total_authors = session.query(func.count(func.distinct(Commit.author_email))).scalar()
            total_repositories = session.query(func.count(Repository.id)).scalar()
            total_lines = session.query(
                func.sum(Commit.lines_added + Commit.lines_deleted)
            ).scalar() or 0

            return {
                'total_commits': total_commits,
                'total_authors': total_authors,
                'total_repositories': total_repositories,
                'total_lines': total_lines
            }
        finally:
            session.close()

    def get_author_statistics(self, start_date=None, end_date=None):
        """Get comprehensive statistics for each author.

        Args:
            start_date: Optional start date for filtering (datetime or date object)
            end_date: Optional end date for filtering (datetime or date object)

        Returns:
            DataFrame with author statistics including commits, lines, PRs, and approvals
        """
        session = get_session(self.engine)
        try:
            # Get commit statistics per author with optional date filtering
            commit_query = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.count(func.distinct(Commit.repository_id)).label('repositories_count')
            )

            # Apply date filters to commits
            if start_date:
                commit_query = commit_query.filter(Commit.commit_date >= start_date)
            if end_date:
                commit_query = commit_query.filter(Commit.commit_date <= end_date)

            commit_stats = commit_query.group_by(
                Commit.author_name,
                Commit.author_email
            ).subquery()

            # Get PR creation statistics per author with optional date filtering
            pr_created_query = session.query(
                PullRequest.author_email,
                func.count(PullRequest.id).label('total_prs_created')
            )

            # Apply date filters to PRs
            if start_date:
                pr_created_query = pr_created_query.filter(PullRequest.created_date >= start_date)
            if end_date:
                pr_created_query = pr_created_query.filter(PullRequest.created_date <= end_date)

            pr_created_stats = pr_created_query.group_by(
                PullRequest.author_email
            ).subquery()

            # Get PR approval statistics per author with optional date filtering
            pr_approval_query = session.query(
                PRApproval.approver_email,
                func.count(PRApproval.id).label('total_prs_approved')
            )

            # Apply date filters to approvals
            if start_date:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date >= start_date)
            if end_date:
                pr_approval_query = pr_approval_query.filter(PRApproval.approval_date <= end_date)

            pr_approval_stats = pr_approval_query.group_by(
                PRApproval.approver_email
            ).subquery()

            # Combine all statistics
            query = session.query(
                commit_stats.c.author_name,
                commit_stats.c.author_email,
                commit_stats.c.total_commits,
                commit_stats.c.total_lines_added,
                commit_stats.c.total_lines_deleted,
                (commit_stats.c.total_lines_added + commit_stats.c.total_lines_deleted).label('total_lines_changed'),
                commit_stats.c.total_files_changed,
                commit_stats.c.repositories_count,
                func.coalesce(pr_created_stats.c.total_prs_created, 0).label('total_prs_created'),
                func.coalesce(pr_approval_stats.c.total_prs_approved, 0).label('total_prs_approved')
            ).outerjoin(
                pr_created_stats,
                commit_stats.c.author_email == pr_created_stats.c.author_email
            ).outerjoin(
                pr_approval_stats,
                commit_stats.c.author_email == pr_approval_stats.c.approver_email
            ).order_by(
                desc('total_commits')
            )

            results = query.all()

            data = [{
                'Author Name': r.author_name,
                'Email': r.author_email,
                'Total Commits': r.total_commits,
                'Lines Added': r.total_lines_added or 0,
                'Lines Deleted': r.total_lines_deleted or 0,
                'Total Lines Changed': r.total_lines_changed or 0,
                'Files Changed': r.total_files_changed or 0,
                'Repositories': r.repositories_count,
                'PRs Created': r.total_prs_created,
                'PRs Approved': r.total_prs_approved
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()


    def get_table_data(self, table_name, limit=1000):
        """Get data from a specific table.

        Args:
            table_name: Name of the table to query
            limit: Maximum number of rows to return

        Returns:
            DataFrame with table data
        """
        session = get_session(self.engine)
        try:
            # Map table names to models
            table_models = {
                'repositories': Repository,
                'commits': Commit,
                'pull_requests': PullRequest,
                'pr_approvals': PRApproval,
                'staff_details': StaffDetails
            }

            if table_name not in table_models:
                return pd.DataFrame()

            model = table_models[table_name]
            query = session.query(model).limit(limit)

            # Convert to DataFrame
            data = []
            for row in query:
                row_dict = {}
                for column in row.__table__.columns:
                    row_dict[column.name] = getattr(row, column.name)
                data.append(row_dict)

            return pd.DataFrame(data)
        finally:
            session.close()

    def execute_sql_query(self, sql_query):
        """Execute a SQL query and return results.

        Args:
            sql_query: SQL query string

        Returns:
            Tuple of (DataFrame with results, error message if any)
        """
        try:
            # Execute query and return as DataFrame
            df = pd.read_sql_query(sql_query, self.engine)
            return df, None
        except Exception as e:
            return pd.DataFrame(), str(e)

    def get_table_info(self):
        """Get information about all tables.

        Returns:
            Dictionary with table names and row counts
        """
        session = get_session(self.engine)
        try:
            table_info = {
                'repositories': session.query(Repository).count(),
                'commits': session.query(Commit).count(),
                'pull_requests': session.query(PullRequest).count(),
                'pr_approvals': session.query(PRApproval).count(),
                'staff_details': session.query(StaffDetails).count(),
                'author_staff_mapping': session.query(AuthorStaffMapping).count()
            }
            return table_info
        finally:
            session.close()

    def get_distinct_authors(self):
        """Get distinct author names and emails from commits.

        Returns:
            DataFrame with author names and emails
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('commit_count')
            ).group_by(
                Commit.author_name,
                Commit.author_email
            ).order_by(
                Commit.author_name
            )

            results = query.all()
            data = [{
                'Author Name': r.author_name,
                'Email': r.author_email,
                'Commits': r.commit_count
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_staff_list(self):
        """Get list of staff from staff_details.

        Returns:
            DataFrame with staff information
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                StaffDetails.bank_id_1,
                StaffDetails.staff_id,
                StaffDetails.staff_name,
                StaffDetails.email_address,
                StaffDetails.tech_unit
            ).filter(
                StaffDetails.bank_id_1.isnot(None)
            ).order_by(
                StaffDetails.staff_name
            )

            results = query.all()
            data = [{
                'Bank ID': r.bank_id_1,
                'Staff ID': r.staff_id,
                'Staff Name': r.staff_name,
                'Email': r.email_address,
                'Tech Unit': r.tech_unit
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def get_existing_mappings(self):
        """Get existing author-staff mappings.

        Returns:
            DataFrame with existing mappings
        """
        session = get_session(self.engine)
        try:
            query = session.query(
                AuthorStaffMapping.author_name,
                AuthorStaffMapping.author_email,
                AuthorStaffMapping.bank_id_1,
                AuthorStaffMapping.staff_id,
                AuthorStaffMapping.staff_name,
                AuthorStaffMapping.mapped_date,
                AuthorStaffMapping.notes
            ).order_by(
                AuthorStaffMapping.author_name
            )

            results = query.all()
            data = [{
                'Author Name': r.author_name,
                'Author Email': r.author_email,
                'Bank ID': r.bank_id_1,
                'Staff ID': r.staff_id,
                'Staff Name': r.staff_name,
                'Mapped Date': r.mapped_date,
                'Notes': r.notes
            } for r in results]

            return pd.DataFrame(data)
        finally:
            session.close()

    def save_author_staff_mapping(self, author_name, author_email, bank_id_1, staff_id, staff_name, notes=''):
        """Save author-staff mapping to database.

        Args:
            author_name: Author name from commits
            author_email: Author email
            bank_id_1: Bank ID from staff details
            staff_id: Staff ID
            staff_name: Staff name
            notes: Optional notes

        Returns:
            Tuple of (success: bool, message: str)
        """
        session = get_session(self.engine)
        try:
            # Check if mapping already exists
            existing = session.query(AuthorStaffMapping).filter_by(
                author_name=author_name
            ).first()

            if existing:
                # Update existing mapping
                existing.author_email = author_email
                existing.bank_id_1 = bank_id_1
                existing.staff_id = staff_id
                existing.staff_name = staff_name
                existing.mapped_date = datetime.utcnow()
                existing.notes = notes
                session.commit()
                return True, f"Updated mapping for {author_name}"
            else:
                # Create new mapping
                mapping = AuthorStaffMapping(
                    author_name=author_name,
                    author_email=author_email,
                    bank_id_1=bank_id_1,
                    staff_id=staff_id,
                    staff_name=staff_name,
                    notes=notes
                )
                session.add(mapping)
                session.commit()
                return True, f"Created mapping for {author_name}"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()

    def delete_author_staff_mapping(self, author_name):
        """Delete author-staff mapping.

        Args:
            author_name: Author name to delete mapping for

        Returns:
            Tuple of (success: bool, message: str)
        """
        session = get_session(self.engine)
        try:
            mapping = session.query(AuthorStaffMapping).filter_by(
                author_name=author_name
            ).first()

            if mapping:
                session.delete(mapping)
                session.commit()
                return True, f"Deleted mapping for {author_name}"
            else:
                return False, f"No mapping found for {author_name}"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()


def main():
    """Main dashboard application."""
    st.set_page_config(
        page_title="Git History Dashboard",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Git History Analysis Dashboard")

    dashboard = GitHistoryDashboard()

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Authors Analytics", "Top 10 Commits", "Top PR Approvers", "Detailed Commits View", "Detailed PRs View", "Author-Staff Mapping", "Table Viewer", "SQL Executor"]
    )

    # Overview Page
    if page == "Overview":
        st.header("Overview")

        stats = dashboard.get_commit_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Commits", f"{stats['total_commits']:,}")
        with col2:
            st.metric("Total Authors", f"{stats['total_authors']:,}")
        with col3:
            st.metric("Total Repositories", f"{stats['total_repositories']:,}")
        with col4:
            st.metric("Total Lines Changed", f"{stats['total_lines']:,}")

        st.markdown("---")
        st.info("Use the sidebar to navigate to different views.")

    # Authors Analytics Page
    elif page == "Authors Analytics":
        st.header("👨‍💻 Authors Analytics")
        st.markdown("Comprehensive statistics for all contributors")

        # Date range filter
        st.subheader("📅 Date Range Filter")
        col1, col2, col3 = st.columns([2, 2, 1])

        # Get min and max dates from commits
        session = get_session(dashboard.engine)
        try:
            min_commit_date = session.query(func.min(Commit.commit_date)).scalar()
            max_commit_date = session.query(func.max(Commit.commit_date)).scalar()
        finally:
            session.close()

        # Set default dates
        if min_commit_date and max_commit_date:
            default_start = min_commit_date.date() if hasattr(min_commit_date, 'date') else min_commit_date
            default_end = max_commit_date.date() if hasattr(max_commit_date, 'date') else max_commit_date
        else:
            # Fallback if no commits exist
            from datetime import date, timedelta
            default_end = date.today()
            default_start = default_end - timedelta(days=365)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=default_start,
                min_value=default_start,
                max_value=default_end
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=default_end,
                min_value=default_start,
                max_value=default_end
            )

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.button("🔄 Reset Dates"):
                start_date = default_start
                end_date = default_end
                st.rerun()

        # Show selected date range info
        if start_date and end_date:
            date_diff = (end_date - start_date).days
            st.info(f"📊 Analyzing data from **{start_date}** to **{end_date}** ({date_diff} days)")

        st.markdown("---")

        # Convert dates to datetime for query
        from datetime import datetime as dt
        start_datetime = dt.combine(start_date, dt.min.time()) if start_date else None
        end_datetime = dt.combine(end_date, dt.max.time()) if end_date else None

        # Get author statistics with date filter
        df = dashboard.get_author_statistics(start_date=start_datetime, end_date=end_datetime)

        if df.empty:
            st.warning("No author data available for the selected date range.")
        else:
            # Summary metrics
            st.subheader("Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Authors", len(df))
            with col2:
                st.metric("Total Commits", f"{df['Total Commits'].sum():,}")
            with col3:
                st.metric("Total Lines Changed", f"{df['Total Lines Changed'].sum():,}")
            with col4:
                st.metric("Total PRs", f"{df['PRs Created'].sum() + df['PRs Approved'].sum():,.0f}")

            st.markdown("---")

            # Top contributors by commits
            st.subheader("📊 Top Contributors by Commits")
            top_by_commits = df.nlargest(10, 'Total Commits')
            fig = px.bar(
                top_by_commits,
                x='Author Name',
                y='Total Commits',
                title='Top 10 Contributors by Number of Commits',
                labels={'Total Commits': 'Number of Commits'},
                color='Total Commits',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, width='stretch')

            # Top contributors by lines changed
            st.subheader("📈 Top Contributors by Lines Changed")
            top_by_lines = df.nlargest(10, 'Total Lines Changed')
            fig2 = px.bar(
                top_by_lines,
                x='Author Name',
                y=['Lines Added', 'Lines Deleted'],
                title='Top 10 Contributors by Lines Changed',
                labels={'value': 'Lines', 'variable': 'Type'},
                barmode='group',
                color_discrete_map={'Lines Added': '#2ecc71', 'Lines Deleted': '#e74c3c'}
            )
            st.plotly_chart(fig2, width='stretch')

            # Comprehensive statistics table
            st.subheader("📋 Detailed Author Statistics")

            # Add sorting options
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox(
                    "Sort by",
                    ['Total Commits', 'Total Lines Changed', 'Lines Added', 'Lines Deleted',
                     'Files Changed', 'PRs Created', 'PRs Approved', 'Repositories']
                )
            with col2:
                sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

            # Sort dataframe
            sorted_df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))

            # Display table
            st.dataframe(sorted_df, width='stretch', height=500)

            # Download button
            csv = sorted_df.to_csv(index=False)
            st.download_button(
                label="Download Author Statistics as CSV",
                data=csv,
                file_name=f"author_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

            # Additional insights
            st.markdown("---")
            st.subheader("💡 Insights")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Most Active Author",
                    df.iloc[0]['Author Name'] if not df.empty else "N/A",
                    f"{df.iloc[0]['Total Commits']:,} commits" if not df.empty else ""
                )

            with col2:
                top_lines_author = df.nlargest(1, 'Total Lines Changed')
                if not top_lines_author.empty:
                    st.metric(
                        "Most Lines Changed",
                        top_lines_author.iloc[0]['Author Name'],
                        f"{top_lines_author.iloc[0]['Total Lines Changed']:,.0f} lines"
                    )

            with col3:
                top_pr_reviewer = df.nlargest(1, 'PRs Approved')
                if not top_pr_reviewer.empty and top_pr_reviewer.iloc[0]['PRs Approved'] > 0:
                    st.metric(
                        "Top PR Reviewer",
                        top_pr_reviewer.iloc[0]['Author Name'],
                        f"{top_pr_reviewer.iloc[0]['PRs Approved']:.0f} approvals"
                    )

    # Top 10 Commits Page
    elif page == "Top 10 Commits":
        st.header("🏆 Top 10 Commits by Lines Changed")

        df = dashboard.get_top_commits_by_lines(10)

        if df.empty:
            st.warning("No commit data available.")
        else:
            # Bar chart
            fig = px.bar(
                df,
                x='Author',
                y='Total Lines',
                color='Repository',
                title='Top 10 Commits by Total Lines Changed',
                hover_data=['Commit Hash', 'Date', 'Files Changed'],
                labels={'Total Lines': 'Total Lines Changed'}
            )
            st.plotly_chart(fig, width='stretch')

            # Detailed table
            st.subheader("Detailed Information")
            display_df = df[[
                'Commit Hash', 'Author', 'Date', 'Repository',
                'Lines Added', 'Lines Deleted', 'Total Lines',
                'Files Changed', 'Message'
            ]]
            st.dataframe(display_df, width='stretch', height=400)

    # Top PR Approvers Page
    elif page == "Top PR Approvers":
        st.header("👥 Top PR Approvers")

        df = dashboard.get_top_pr_approvers(10)

        if df.empty:
            st.warning("No PR approval data available.")
        else:
            # Horizontal bar chart
            fig = px.bar(
                df,
                y='Approver Name',
                x='Total Approvals',
                orientation='h',
                title='Top 10 PR Approvers',
                labels={'Total Approvals': 'Number of Approvals'},
                color='Total Approvals',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, width='stretch')

            # Detailed table
            st.subheader("Detailed Information")
            st.dataframe(df, width='stretch', height=400)

    # Detailed Commits View
    elif page == "Detailed Commits View":
        st.header("📝 Detailed Commits View")

        df = dashboard.get_all_commits()

        if df.empty:
            st.warning("No commit data available.")
        else:
            # Filters
            st.subheader("Filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                authors = ['All'] + sorted(df['Author'].unique().tolist())
                selected_author = st.selectbox("Author", authors)

            with col2:
                repos = ['All'] + sorted(df['Full Repo Name'].unique().tolist())
                selected_repo = st.selectbox("Repository", repos)

            with col3:
                branches = ['All'] + sorted(df['Branch'].unique().tolist())
                selected_branch = st.selectbox("Branch", branches)

            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                min_date = df['Date'].min()
                start_date = st.date_input("Start Date", min_date)
            with col2:
                max_date = df['Date'].max()
                end_date = st.date_input("End Date", max_date)

            # Apply filters
            filtered_df = df.copy()
            if selected_author != 'All':
                filtered_df = filtered_df[filtered_df['Author'] == selected_author]
            if selected_repo != 'All':
                filtered_df = filtered_df[filtered_df['Full Repo Name'] == selected_repo]
            if selected_branch != 'All':
                filtered_df = filtered_df[filtered_df['Branch'] == selected_branch]

            filtered_df = filtered_df[
                (filtered_df['Date'].dt.date >= start_date) &
                (filtered_df['Date'].dt.date <= end_date)
            ]

            # Sorting
            st.subheader("Sorting")
            sort_columns = ['Date', 'Total Lines', 'Lines Added', 'Lines Deleted', 'Files Changed']
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox("Sort by", sort_columns)
            with col2:
                sort_order = st.radio("Order", ["Descending", "Ascending"])

            filtered_df = filtered_df.sort_values(
                by=sort_by,
                ascending=(sort_order == "Ascending")
            )

            # Display results
            st.subheader(f"Results ({len(filtered_df)} commits)")

            display_df = filtered_df[[
                'Commit Hash', 'Author', 'Date', 'Full Repo Name',
                'Branch', 'Lines Added', 'Lines Deleted', 'Total Lines',
                'Files Changed', 'Message'
            ]]

            st.dataframe(display_df, width='stretch', height=500)

            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"commits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Detailed PRs View
    elif page == "Detailed PRs View":
        st.header("🔀 Detailed Pull Requests View")

        df = dashboard.get_all_pull_requests()

        if df.empty:
            st.warning("No pull request data available.")
        else:
            # Filters
            st.subheader("Filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                authors = ['All'] + sorted(df['Author'].unique().tolist())
                selected_author = st.selectbox("Author", authors)

            with col2:
                repos = ['All'] + sorted(df['Full Repo Name'].unique().tolist())
                selected_repo = st.selectbox("Repository", repos)

            with col3:
                states = ['All'] + sorted(df['State'].unique().tolist())
                selected_state = st.selectbox("State", states)

            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                min_date = df['Created Date'].min()
                start_date = st.date_input("Start Date", min_date)
            with col2:
                max_date = df['Created Date'].max()
                end_date = st.date_input("End Date", max_date)

            # Apply filters
            filtered_df = df.copy()
            if selected_author != 'All':
                filtered_df = filtered_df[filtered_df['Author'] == selected_author]
            if selected_repo != 'All':
                filtered_df = filtered_df[filtered_df['Full Repo Name'] == selected_repo]
            if selected_state != 'All':
                filtered_df = filtered_df[filtered_df['State'] == selected_state]

            filtered_df = filtered_df[
                (filtered_df['Created Date'].dt.date >= start_date) &
                (filtered_df['Created Date'].dt.date <= end_date)
            ]

            # Sorting
            st.subheader("Sorting")
            sort_columns = ['Created Date', 'Total Lines', 'Lines Added', 'Lines Deleted', 'Approvals', 'Commits']
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox("Sort by", sort_columns)
            with col2:
                sort_order = st.radio("Order", ["Descending", "Ascending"])

            filtered_df = filtered_df.sort_values(
                by=sort_by,
                ascending=(sort_order == "Ascending")
            )

            # Display results
            st.subheader(f"Results ({len(filtered_df)} pull requests)")

            display_df = filtered_df[[
                'PR Number', 'Title', 'Author', 'Created Date', 'State',
                'Full Repo Name', 'Source Branch', 'Target Branch',
                'Lines Added', 'Lines Deleted', 'Total Lines',
                'Commits', 'Approvals'
            ]]

            st.dataframe(display_df, width='stretch', height=500)

            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"pull_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Author-Staff Mapping Page
    elif page == "Author-Staff Mapping":
        st.header("👥 Author-Staff Mapping")
        st.markdown("Map commit authors to staff members from staff details")

        # Ensure database tables exist
        init_database(dashboard.engine)

        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Create Mapping", "View Mappings", "Bulk Operations"])

        with tab1:
            st.subheader("🔗 Create New Mapping")

            # Get authors and staff data
            authors_df = dashboard.get_distinct_authors()
            staff_df = dashboard.get_staff_list()
            existing_mappings_df = dashboard.get_existing_mappings()

            if authors_df.empty:
                st.warning("No commit authors found. Please extract commits first.")
            elif staff_df.empty:
                st.warning("No staff details found. Please import staff details first using CLI: `python cli.py import-staff staff_data.xlsx`")
            else:
                # Filter out already mapped authors
                if not existing_mappings_df.empty:
                    mapped_authors = existing_mappings_df['Author Name'].tolist()
                    unmapped_authors_df = authors_df[~authors_df['Author Name'].isin(mapped_authors)]
                else:
                    unmapped_authors_df = authors_df

                # Two-column layout
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📝 Select Author")
                    st.info(f"Total Authors: {len(authors_df)} | Unmapped: {len(unmapped_authors_df)}")

                    # Author selection
                    if not unmapped_authors_df.empty:
                        selected_author = st.selectbox(
                            "Author Name",
                            options=unmapped_authors_df['Author Name'].tolist(),
                            format_func=lambda x: f"{x} ({unmapped_authors_df[unmapped_authors_df['Author Name']==x]['Commits'].iloc[0]} commits)"
                        )

                        # Show author details
                        author_row = unmapped_authors_df[unmapped_authors_df['Author Name'] == selected_author].iloc[0]
                        st.text_input("Author Email", value=author_row['Email'], disabled=True)
                        st.metric("Total Commits", f"{author_row['Commits']:,}")
                    else:
                        st.success("All authors have been mapped!")
                        selected_author = None

                with col2:
                    st.markdown("### 👤 Select Staff Member")
                    st.info(f"Total Staff: {len(staff_df)}")

                    if selected_author:
                        # Staff selection with search
                        search_term = st.text_input("🔍 Search Staff (by name or email)", "")

                        if search_term:
                            filtered_staff = staff_df[
                                staff_df['Staff Name'].str.contains(search_term, case=False, na=False) |
                                staff_df['Email'].str.contains(search_term, case=False, na=False)
                            ]
                        else:
                            filtered_staff = staff_df

                        if not filtered_staff.empty:
                            selected_staff_idx = st.selectbox(
                                "Staff Member",
                                options=range(len(filtered_staff)),
                                format_func=lambda x: f"{filtered_staff.iloc[x]['Staff Name']} ({filtered_staff.iloc[x]['Bank ID']})"
                            )

                            staff_row = filtered_staff.iloc[selected_staff_idx]

                            # Show staff details
                            st.text_input("Bank ID", value=staff_row['Bank ID'], disabled=True, key="bank_id_display")
                            st.text_input("Staff ID", value=staff_row['Staff ID'], disabled=True)
                            st.text_input("Staff Email", value=staff_row['Email'], disabled=True)
                            st.text_input("Tech Unit", value=staff_row['Tech Unit'], disabled=True)
                        else:
                            st.warning("No staff found matching search criteria")
                            staff_row = None
                    else:
                        staff_row = None

                # Mapping section
                if selected_author and staff_row is not None:
                    st.markdown("---")
                    st.subheader("💾 Save Mapping")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        notes = st.text_area(
                            "Notes (optional)",
                            placeholder="Add any notes about this mapping...",
                            height=100
                        )

                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("✅ Save Mapping", type="primary", use_container_width=True):
                            success, message = dashboard.save_author_staff_mapping(
                                author_name=selected_author,
                                author_email=author_row['Email'],
                                bank_id_1=staff_row['Bank ID'],
                                staff_id=staff_row['Staff ID'],
                                staff_name=staff_row['Staff Name'],
                                notes=notes
                            )

                            if success:
                                st.success(message)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(message)

        with tab2:
            st.subheader("📊 Existing Mappings")

            existing_mappings_df = dashboard.get_existing_mappings()

            if existing_mappings_df.empty:
                st.info("No mappings created yet. Use the 'Create Mapping' tab to get started.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Mappings", len(existing_mappings_df))
                with col2:
                    authors_count = dashboard.get_distinct_authors().shape[0]
                    mapped_pct = (len(existing_mappings_df) / authors_count * 100) if authors_count > 0 else 0
                    st.metric("Mapping Coverage", f"{mapped_pct:.1f}%")
                with col3:
                    recent_mapping = existing_mappings_df['Mapped Date'].max()
                    if pd.notna(recent_mapping):
                        st.metric("Last Mapping", recent_mapping.strftime('%Y-%m-%d'))

                st.markdown("---")

                # Display mappings table
                display_df = existing_mappings_df[[
                    'Author Name', 'Author Email', 'Bank ID', 'Staff ID',
                    'Staff Name', 'Mapped Date', 'Notes'
                ]]

                st.dataframe(display_df, width='stretch', height=400)

                # Delete mapping functionality
                st.markdown("---")
                st.subheader("🗑️ Delete Mapping")
                col1, col2 = st.columns([3, 1])
                with col1:
                    delete_author = st.selectbox(
                        "Select author mapping to delete",
                        options=existing_mappings_df['Author Name'].tolist()
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                        success, message = dashboard.delete_author_staff_mapping(delete_author)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

                # Export mappings
                st.markdown("---")
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Mappings as CSV",
                    data=csv,
                    file_name=f"author_staff_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with tab3:
            st.subheader("⚡ Bulk Operations")

            st.markdown("### Auto-Match by Email")
            st.info("Automatically map authors to staff members when emails match")

            authors_df = dashboard.get_distinct_authors()
            staff_df = dashboard.get_staff_list()
            existing_mappings_df = dashboard.get_existing_mappings()

            if not authors_df.empty and not staff_df.empty:
                # Find potential matches
                potential_matches = []

                # Filter unmapped authors
                if not existing_mappings_df.empty:
                    mapped_authors = existing_mappings_df['Author Name'].tolist()
                    unmapped_authors = authors_df[~authors_df['Author Name'].isin(mapped_authors)]
                else:
                    unmapped_authors = authors_df

                for _, author in unmapped_authors.iterrows():
                    author_email = str(author['Email']).lower().strip()
                    matching_staff = staff_df[staff_df['Email'].str.lower().str.strip() == author_email]

                    if not matching_staff.empty:
                        staff_match = matching_staff.iloc[0]
                        potential_matches.append({
                            'Author Name': author['Author Name'],
                            'Author Email': author['Email'],
                            'Staff Name': staff_match['Staff Name'],
                            'Bank ID': staff_match['Bank ID'],
                            'Staff ID': staff_match['Staff ID'],
                            'Match Type': 'Email Match'
                        })

                if potential_matches:
                    matches_df = pd.DataFrame(potential_matches)
                    st.success(f"Found {len(potential_matches)} potential email matches")
                    st.dataframe(matches_df, width='stretch')

                    if st.button("✅ Apply All Email Matches", type="primary"):
                        success_count = 0
                        error_count = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for idx, match in enumerate(potential_matches):
                            status_text.text(f"Processing {idx+1}/{len(potential_matches)}: {match['Author Name']}")

                            success, message = dashboard.save_author_staff_mapping(
                                author_name=match['Author Name'],
                                author_email=match['Author Email'],
                                bank_id_1=match['Bank ID'],
                                staff_id=match['Staff ID'],
                                staff_name=match['Staff Name'],
                                notes='Auto-matched by email'
                            )

                            if success:
                                success_count += 1
                            else:
                                error_count += 1

                            progress_bar.progress((idx + 1) / len(potential_matches))

                        status_text.empty()
                        progress_bar.empty()

                        if success_count > 0:
                            st.success(f"✅ Successfully created {success_count} mappings")
                            if error_count > 0:
                                st.warning(f"⚠️ {error_count} mappings failed")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("No mappings could be created")
                else:
                    st.info("No email matches found. All unmapped authors have emails that don't match staff records.")
            else:
                st.warning("Need both commit authors and staff details to perform bulk operations")

            # Manual bulk upload
            st.markdown("---")
            st.markdown("### 📤 Upload Mappings from CSV")
            st.info("Upload a CSV file with columns: Author Name, Author Email, Bank ID, Staff ID, Staff Name, Notes")

            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            if uploaded_file:
                try:
                    upload_df = pd.read_csv(uploaded_file)
                    required_cols = ['Author Name', 'Bank ID', 'Staff ID', 'Staff Name']

                    if all(col in upload_df.columns for col in required_cols):
                        st.dataframe(upload_df.head(), width='stretch')

                        if st.button("📥 Import Mappings", type="primary"):
                            success_count = 0
                            error_count = 0

                            progress_bar = st.progress(0)
                            for idx, row in upload_df.iterrows():
                                success, _ = dashboard.save_author_staff_mapping(
                                    author_name=row['Author Name'],
                                    author_email=row.get('Author Email', ''),
                                    bank_id_1=row['Bank ID'],
                                    staff_id=row['Staff ID'],
                                    staff_name=row['Staff Name'],
                                    notes=row.get('Notes', '')
                                )
                                if success:
                                    success_count += 1
                                else:
                                    error_count += 1
                                progress_bar.progress((idx + 1) / len(upload_df))

                            progress_bar.empty()
                            st.success(f"Imported {success_count} mappings ({error_count} errors)")
                            st.rerun()
                    else:
                        st.error(f"CSV must have columns: {', '.join(required_cols)}")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")

    # Table Viewer Page
    elif page == "Table Viewer":
        st.header("📋 Database Table Viewer")
        st.markdown("Browse all database tables and export data")

        # Get table information
        table_info = dashboard.get_table_info()

        # Display table overview
        st.subheader("Tables Overview")
        overview_data = []
        for table_name, row_count in table_info.items():
            overview_data.append({
                'Table Name': table_name,
                'Row Count': f"{row_count:,}"
            })
        overview_df = pd.DataFrame(overview_data)
        st.dataframe(overview_df, width='stretch', hide_index=True)

        st.markdown("---")

        # Table selection
        st.subheader("View Table Data")
        col1, col2 = st.columns([3, 1])

        with col1:
            selected_table = st.selectbox(
                "Select Table",
                list(table_info.keys()),
                format_func=lambda x: f"{x} ({table_info[x]:,} rows)"
            )

        with col2:
            row_limit = st.number_input(
                "Limit Rows",
                min_value=10,
                max_value=10000,
                value=1000,
                step=100
            )

        if st.button("Load Table Data", type="primary"):
            with st.spinner(f"Loading data from {selected_table}..."):
                df = dashboard.get_table_data(selected_table, limit=row_limit)

                if df.empty:
                    st.warning(f"No data found in table '{selected_table}'")
                else:
                    st.success(f"Loaded {len(df):,} rows from {selected_table}")

                    # Display data
                    st.dataframe(df, width='stretch', height=500)

                    # Table statistics
                    st.subheader("Table Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Rows", f"{len(df):,}")
                    with col2:
                        st.metric("Total Columns", len(df.columns))
                    with col3:
                        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
                        st.metric("Memory Usage", f"{memory_usage:.2f} MB")

                    # Column information
                    with st.expander("Column Information"):
                        col_info = []
                        for col in df.columns:
                            col_info.append({
                                'Column Name': col,
                                'Data Type': str(df[col].dtype),
                                'Non-Null Count': f"{df[col].count():,}",
                                'Null Count': f"{df[col].isnull().sum():,}"
                            })
                        col_info_df = pd.DataFrame(col_info)
                        st.dataframe(col_info_df, width='stretch', hide_index=True)

                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Table as CSV",
                        data=csv,
                        file_name=f"{selected_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

    # SQL Executor Page
    elif page == "SQL Executor":
        st.header("⚡ SQL Query Executor")
        st.markdown("Execute custom SQL queries against the database")

        # Warning message
        st.warning("⚠️ **Read-only queries recommended.** Use caution with UPDATE, DELETE, or INSERT statements.")

        # Database info
        with st.expander("📊 Database Schema Information"):
            table_info = dashboard.get_table_info()

            st.subheader("Available Tables")
            for table_name, row_count in table_info.items():
                st.markdown(f"**{table_name}** - {row_count:,} rows")

            st.markdown("---")
            st.subheader("Table Schemas")

            # Repositories
            st.markdown("**repositories**")
            st.code("""
id              INTEGER PRIMARY KEY
project_key     VARCHAR(255)
slug_name       VARCHAR(255)
clone_url       VARCHAR(500)
created_at      DATETIME
            """, language="sql")

            # Commits
            st.markdown("**commits**")
            st.code("""
id              INTEGER PRIMARY KEY
repository_id   INTEGER (FK -> repositories.id)
commit_hash     VARCHAR(40) UNIQUE
author_name     VARCHAR(255)
author_email    VARCHAR(255)
committer_name  VARCHAR(255)
committer_email VARCHAR(255)
commit_date     DATETIME
message         TEXT
lines_added     INTEGER
lines_deleted   INTEGER
files_changed   INTEGER
branch          VARCHAR(255)
            """, language="sql")

            # Pull Requests
            st.markdown("**pull_requests**")
            st.code("""
id              INTEGER PRIMARY KEY
repository_id   INTEGER (FK -> repositories.id)
pr_number       INTEGER
title           VARCHAR(500)
description     TEXT
author_name     VARCHAR(255)
author_email    VARCHAR(255)
created_date    DATETIME
merged_date     DATETIME
state           VARCHAR(50)
source_branch   VARCHAR(255)
target_branch   VARCHAR(255)
lines_added     INTEGER
lines_deleted   INTEGER
commits_count   INTEGER
            """, language="sql")

            # PR Approvals
            st.markdown("**pr_approvals**")
            st.code("""
id              INTEGER PRIMARY KEY
pull_request_id INTEGER (FK -> pull_requests.id)
approver_name   VARCHAR(255)
approver_email  VARCHAR(255)
approval_date   DATETIME
            """, language="sql")

            # Staff Details
            st.markdown("**staff_details**")
            st.code("""
id                          INTEGER PRIMARY KEY
bank_id_1                   VARCHAR(50)
staff_id                    VARCHAR(50)
staff_name                  VARCHAR(255)
email_address               VARCHAR(255)
staff_start_date            DATE
staff_end_date              DATE
... (71 fields total - see models.py for complete list)
            """, language="sql")

        # Query input with examples
        st.subheader("SQL Query")

        # Sample queries
        sample_queries = {
            "Select All Repositories": "SELECT * FROM repositories LIMIT 10;",
            "Top 10 Authors by Commits": """SELECT author_name, COUNT(*) as commit_count
FROM commits
GROUP BY author_name
ORDER BY commit_count DESC
LIMIT 10;""",
            "PRs with Most Approvals": """SELECT pr.pr_number, pr.title, pr.author_name,
       COUNT(pa.id) as approval_count
FROM pull_requests pr
LEFT JOIN pr_approvals pa ON pr.id = pa.pull_request_id
GROUP BY pr.id
ORDER BY approval_count DESC
LIMIT 10;""",
            "Commits by Month": """SELECT strftime('%Y-%m', commit_date) as month,
       COUNT(*) as commits,
       SUM(lines_added) as total_added,
       SUM(lines_deleted) as total_deleted
FROM commits
GROUP BY month
ORDER BY month DESC;""",
            "Staff by Department": "SELECT tech_unit, COUNT(*) as staff_count FROM staff_details GROUP BY tech_unit ORDER BY staff_count DESC;",
            "Join Commits with Repositories": """SELECT r.project_key, r.slug_name,
       COUNT(c.id) as commit_count,
       SUM(c.lines_added + c.lines_deleted) as total_lines_changed
FROM repositories r
LEFT JOIN commits c ON r.id = c.repository_id
GROUP BY r.id
ORDER BY commit_count DESC;"""
        }

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Enter your SQL query below:**")
        with col2:
            selected_sample = st.selectbox(
                "Load Sample Query",
                ["Custom Query"] + list(sample_queries.keys())
            )

        # Set default query
        if selected_sample != "Custom Query":
            default_query = sample_queries[selected_sample]
        else:
            default_query = "SELECT * FROM repositories LIMIT 10;"

        sql_query = st.text_area(
            "SQL Query",
            value=default_query,
            height=200,
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            execute_button = st.button("▶ Execute Query", type="primary")
        with col2:
            if sql_query.strip().upper().startswith(('UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER')):
                st.error("⚠️ Detected potentially destructive query. Use with caution!")

        if execute_button:
            if not sql_query.strip():
                st.error("Please enter a SQL query")
            else:
                with st.spinner("Executing query..."):
                    df, error = dashboard.execute_sql_query(sql_query)

                    if error:
                        st.error(f"❌ Query Error: {error}")
                    elif df.empty:
                        st.info("✓ Query executed successfully but returned no results")
                    else:
                        st.success(f"✓ Query executed successfully - {len(df):,} rows returned")

                        # Display results
                        st.subheader("Query Results")
                        st.dataframe(df, width='stretch', height=400)

                        # Result statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", f"{len(df):,}")
                        with col2:
                            st.metric("Columns", len(df.columns))
                        with col3:
                            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
                            st.metric("Memory", f"{memory_usage:.2f} MB")

                        # Download results
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download Results as CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )


if __name__ == '__main__':
    main()
