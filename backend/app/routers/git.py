"""Git helper APIs (e.g., list branches for a GitHub repo)."""

from __future__ import annotations

import logging
import re
import subprocess
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..dependencies.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/git", tags=["git"])

_GITHUB_HTTPS_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
_GITHUB_SSH_RE = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    re.IGNORECASE,
)
_GITHUB_SSH_URL_RE = re.compile(
    r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


class GitBranchesResponse(BaseModel):
    repo_url: str = Field(..., description="Normalized HTTPS repo URL")
    branches: List[str] = Field(..., description="Branch names")
    default_branch: Optional[str] = Field(
        None, description="Best-effort default branch guess (main/master/first)"
    )


def _normalize_github_repo_url(repo_url: str) -> str:
    url = (repo_url or "").strip()
    if not url:
        raise ValueError("repo_url is required")

    m = _GITHUB_HTTPS_RE.match(url) or _GITHUB_SSH_RE.match(url) or _GITHUB_SSH_URL_RE.match(url)
    if not m:
        raise ValueError(
            "Only GitHub repository URLs are supported. "
            "Expected https://github.com/<owner>/<repo>(.git) or git@github.com:<owner>/<repo>(.git)"
        )

    owner = m.group("owner")
    repo = m.group("repo")
    # Defensive: strip trailing ".git" if regex didn't already exclude it.
    if repo.lower().endswith(".git"):
        repo = repo[:-4]

    return f"https://github.com/{owner}/{repo}.git"


def _sort_branches(branches: List[str]) -> List[str]:
    uniq = sorted(set(b for b in branches if b))
    preferred = []
    for name in ("main", "master"):
        if name in uniq:
            preferred.append(name)
            uniq.remove(name)
    return preferred + uniq


@router.get("/branches", response_model=GitBranchesResponse)
async def list_branches(
    repo_url: str,
    current_user: User = Depends(get_current_user),
):
    """List remote branches for a GitHub repository.

    Notes:
    - Uses `git ls-remote` (no clone required).
    - Restricts to GitHub URLs to avoid SSRF/protocol abuse.
    """
    _ = current_user  # auth gate (and future rate-limiting hook)

    try:
        normalized = _normalize_github_repo_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        # `--refs` avoids dereferenced tags; `--heads` limits to branches.
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "--refs", normalized],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out while fetching branches. Please try again.",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="git is not available on the server",
        )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        logger.warning("git ls-remote failed: %s", stderr or stdout)
        if "Could not resolve host" in stderr or "Could not resolve host" in stdout:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to resolve GitHub host from server. Please verify outbound DNS/network.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=stderr or stdout or "Failed to fetch branches",
        )

    branches: List[str] = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        ref = parts[1]
        if not ref.startswith("refs/heads/"):
            continue
        branches.append(ref[len("refs/heads/") :])

    branches_sorted = _sort_branches(branches)
    if not branches_sorted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No branches found (repo may not exist or is not accessible).",
        )

    default_branch = None
    if "main" in branches_sorted:
        default_branch = "main"
    elif "master" in branches_sorted:
        default_branch = "master"
    else:
        default_branch = branches_sorted[0]

    return GitBranchesResponse(
        repo_url=normalized,
        branches=branches_sorted,
        default_branch=default_branch,
    )
