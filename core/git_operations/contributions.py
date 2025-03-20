import os
import shutil

from api.data_db import get_commits_from_db
from config.settings import TEMP_FILES_BASE_PATH
from core.git_operations import get_repo
from .diff import get_contributions_from_diffs
from collections import defaultdict
from datetime import datetime, timedelta

def create_temp_dir():
    if os.path.exists(TEMP_FILES_BASE_PATH):
        shutil.rmtree(TEMP_FILES_BASE_PATH)
    os.mkdir(TEMP_FILES_BASE_PATH)

def extract_contributions(repo_path, commit_limit=None, skip=0, fetch_updates=False,):
    repo = get_repo(repo_path)
    if fetch_updates:
        repo.remotes.origin.fetch()
    repo_name = repo.remotes['origin'].url.split('/')[-1].replace('.git', '')
    dbcommits = get_commits_from_db(repo_name)
    processed_commits = []
    for dcommit in dbcommits:
        processed_commits.append(dcommit['sha'])

    create_temp_dir()

    contributions = []

    # Iterate over commits in the active branch
    for commit in repo.iter_commits(max_count=commit_limit, skip=skip):
        if commit.hexsha in processed_commits:
            continue

        if len(commit.parents) == 1:
            # This is a non-merge commit
            parent_commit = commit.parents[0]
            diffs = parent_commit.diff(commit, create_patch=True)
        elif len(commit.parents) == 0:
            # For the first commit, we don't have a parent commit
            diffs = commit.diff(None, create_patch=True)
        else:
            # This is a merge commit
            continue

        contributions += get_contributions_from_diffs(commit, diffs)

    return contributions

'''
def extract_contributions(repo_path, commit_limit=None, skip=0, fetch_updates=False):
    repo = get_repo(repo_path)
    if fetch_updates:
        repo.remotes.origin.fetch()
    repo_name = repo.remotes['origin'].url.split('/')[-1].replace('.git', '')
    dbcommits = get_commits_from_db(repo_name)
    processed_commits = []
    for dcommit in dbcommits:
        processed_commits.append(dcommit['sha'])

    create_temp_dir()

    contributions = []

    now = datetime.now()

    # Loop through each month based on commit_limit.
    for month_offset in range(commit_limit):
        # Calculate the current month.
        current_month = now - timedelta(days=30 * month_offset)  # Approximation for month start

        # Calculate the start and end of the month.
        start_of_month = current_month.replace(day=1)
        if current_month.month == 12:
            end_of_month = current_month.replace(day=1, year=current_month.year + 1, month=1)
        else:
            end_of_month = current_month.replace(day=1, month=current_month.month + 1)

        # Get all commits that occurred during the current month.
        commits_in_month = [
            c for c in repo.iter_commits(since=start_of_month, until=end_of_month)
        ]

        # Sort commits by date
        commits_in_month.sort(key=lambda commit: commit.committed_datetime)

        # Group commits by day
        commits_by_day = defaultdict(list)
        for commit in commits_in_month:
            commits_by_day[commit.committed_datetime.date()].append(commit)

        # Get the first 7 days with commits.
        days_with_commits = list(commits_by_day.keys())
        days_with_commits.sort()

        # Select the first 7 days.
        first_7_days_with_commits = days_with_commits[:7]

        # Create a list of commits to process from the first 7 days
        commits_to_process = []
        for day in first_7_days_with_commits:
            commits_to_process.extend(commits_by_day[day])

        # Iterate through each commit to process.
        for commit in commits_to_process:
            if commit.hexsha in processed_commits:
                continue

            # Get the diffs between the current commit and its parent (if exists).
            if len(commit.parents) == 1:
                parent_commit = commit.parents[0]
                diffs = parent_commit.diff(commit, create_patch=True)
            # Diffs for the initial commit (no parents).
            elif len(commit.parents) == 0:
                diffs = commit.diff(None, create_patch=True)
            else:
                # Skip merge commits (with multiple parents).
                continue  # Skip merge commits

            contributions.extend(get_contributions_from_diffs(commit, diffs))

    return contributions

'''
