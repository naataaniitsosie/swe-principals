"""
Data models for GHArchive events.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventType(Enum):
    """GitHub event types for PR sentiment analysis."""
    PULL_REQUEST = "PullRequestEvent"
    PR_REVIEW = "PullRequestReviewEvent"
    PR_REVIEW_COMMENT = "PullRequestReviewCommentEvent"
    ISSUE_COMMENT = "IssueCommentEvent"


@dataclass(frozen=True)
class Actor:
    """GitHub user/actor."""
    id: int
    login: str
    display_login: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Actor":
        return cls(
            id=data.get("id"),
            login=data.get("login"),
            display_login=data.get("display_login"),
        )


@dataclass(frozen=True)
class PullRequest:
    """Pull request metadata."""
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        return cls(
            id=data.get("id"),
            number=data.get("number"),
            title=data.get("title", ""),
            body=data.get("body"),
            state=data.get("state", ""),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
        )


@dataclass(frozen=True)
class Comment:
    """Comment on a PR or issue."""
    id: int
    body: str
    created_at: datetime
    updated_at: datetime
    user: Actor

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        return cls(
            id=data.get("id"),
            body=data.get("body", ""),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            ),
            user=Actor.from_dict(data.get("user", {})),
        )


@dataclass(frozen=True)
class GitHubEvent:
    """GitHub event from GHArchive JSON."""

    event_id: str
    event_type: EventType
    created_at: datetime
    actor: Actor
    repo_name: str
    payload: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GitHubEvent":
        return cls(
            event_id=data.get("id"),
            event_type=EventType(data.get("type")),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            actor=Actor.from_dict(data.get("actor", {})),
            repo_name=data.get("repo", {}).get("name", ""),
            payload=data.get("payload", {}),
        )

    def extract_text_content(self) -> Optional[str]:
        """Extract text suitable for sentiment analysis."""
        if self.event_type == EventType.PULL_REQUEST:
            pr_data = self.payload.get("pull_request", {})
            title = pr_data.get("title", "")
            body = pr_data.get("body", "")
            return f"{title}\n{body}" if body else title

        elif self.event_type in [
            EventType.PR_REVIEW_COMMENT,
            EventType.ISSUE_COMMENT,
        ]:
            comment = self.payload.get("comment", {})
            return comment.get("body", "")

        elif self.event_type == EventType.PR_REVIEW:
            review = self.payload.get("review", {})
            return review.get("body", "")

        return None
