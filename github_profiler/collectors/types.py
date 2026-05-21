"""Typed contracts for collector outputs"""

from typing import TypedDict


class FileInfo(TypedDict):
    path: str
    size: int
    sha: str
    url: str


class RepoTreeData(TypedDict):
    repo: str
    branch: str
    commit_sha: str
    files: list[FileInfo]
    total_files: int
    collected_at: str


class CommitFileChange(TypedDict):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str


class CommitData(TypedDict):
    sha: str
    author: str | None
    date: str
    message: str
    type: str  # feat/fix/refactor/etc
    files: list[CommitFileChange]
    additions: int
    deletions: int


class CommitCollection(TypedDict):
    repo: str
    commits: list[CommitData]
    total_commits: int
    collected_at: str
