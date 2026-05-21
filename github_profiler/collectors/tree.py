"""GitHub Tree Collector - Recursive tree fetching

SOURCE OF TRUTH FOR TECHNOLOGY DETECTION:
- Complete file tree with all files
- Used to detect technologies via imports, keywords, paths
- Commit patches are NOT used for detection (incomplete context)
"""

from datetime import datetime

from github import Github, Repository

from .types import FileInfo, RepoTreeData


class TreeCollector:
    """Collects repository file tree using recursive Git tree API"""

    def __init__(self, github_client: Github):
        self.client = github_client
        self.max_file_size = 200_000  # 200KB
        self.max_files_per_repo = 2000

    def collect(self, repo: Repository.Repository) -> RepoTreeData:
        """Collect file tree for a repository"""
        try:
            # Get HEAD commit
            head_commit = repo.get_commits().reversed[0]

            # Get recursive tree
            tree = repo.get_git_tree(sha=head_commit.sha, recursive=True)

            files: list[FileInfo] = []
            for item in tree.tree:
                if item.type == "blob":  # file, not directory
                    if item.size <= self.max_file_size:
                        files.append(
                            {"path": item.path, "size": item.size, "sha": item.sha, "url": item.url}
                        )

                    if len(files) >= self.max_files_per_repo:
                        break

            return {
                "repo": repo.full_name,
                "branch": repo.default_branch,
                "commit_sha": head_commit.sha,
                "files": files,
                "total_files": len(files),
                "collected_at": datetime.now().isoformat(),
            }

        except Exception:
            # Return empty tree on error
            return {
                "repo": repo.full_name,
                "branch": repo.default_branch,
                "commit_sha": "",
                "files": [],
                "total_files": 0,
                "collected_at": datetime.now().isoformat(),
            }
