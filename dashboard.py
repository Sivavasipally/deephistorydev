"""Streamlit dashboard for Git history analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func, desc
from datetime import datetime

from config import Config
from models import (
    get_engine, get_session,
    Repository, Commit, PullRequest, PRApproval
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

    def get_author_statistics(self):
        """Get comprehensive statistics for each author.

        Returns:
            DataFrame with author statistics including commits, lines, PRs, and approvals
        """
        session = get_session(self.engine)
        try:
            # Get commit statistics per author
            commit_stats = session.query(
                Commit.author_name,
                Commit.author_email,
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.lines_added).label('total_lines_added'),
                func.sum(Commit.lines_deleted).label('total_lines_deleted'),
                func.sum(Commit.files_changed).label('total_files_changed'),
                func.count(func.distinct(Commit.repository_id)).label('repositories_count')
            ).group_by(
                Commit.author_name,
                Commit.author_email
            ).subquery()

            # Get PR creation statistics per author
            pr_created_stats = session.query(
                PullRequest.author_email,
                func.count(PullRequest.id).label('total_prs_created')
            ).group_by(
                PullRequest.author_email
            ).subquery()

            # Get PR approval statistics per author
            pr_approval_stats = session.query(
                PRApproval.approver_email,
                func.count(PRApproval.id).label('total_prs_approved')
            ).group_by(
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
        ["Overview", "Authors Analytics", "Top 10 Commits", "Top PR Approvers", "Detailed Commits View", "Detailed PRs View"]
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

        df = dashboard.get_author_statistics()

        if df.empty:
            st.warning("No author data available.")
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


if __name__ == '__main__':
    main()
