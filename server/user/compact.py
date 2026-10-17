"""Small read-only responses for recommendation workflows."""

import json
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from client.pool import get_client
from client.user.client import UserClient
from models.types.pagination import PaginatedResponse

Detail = Literal["compact", "detailed"]


def compact_items(items: Any, kind: str, *, total: int | None = None) -> str:
    pagination = None
    if isinstance(items, PaginatedResponse):
        pagination = items.pagination.model_dump()
        items = items.data
    rows = []
    for item in items:
        media = item.get(kind, {})
        row = {
            "id": media.get("ids", {}).get("trakt"),
            "title": media.get("title"),
            "year": media.get("year"),
        }
        for key in ("last_watched_at", "plays", "score"):
            if key in item:
                row[key] = item[key]
        rows.append(row)
    result: dict[str, Any] = {"items": rows, "returned": len(rows)}
    if total is not None:
        result.update(total=total, truncated=len(rows) < total)
    if pagination is not None:
        result["pagination"] = pagination
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def check_watched(client: Any, media_type: str, ids: list[int]) -> dict[str, Any]:
    requested = list(dict.fromkeys(ids))
    found: set[int] = set()
    complete = False
    reason = "not_authenticated"
    try:
        if await client.ensure_authenticated():
            items = await (
                client.get_user_watched_movies()
                if media_type == "movies"
                else client.get_user_watched_shows()
            )
            reason = "read_failed"
            if isinstance(items, list):
                complete = True
                kind = "movie" if media_type == "movies" else "show"
                for item in items:
                    identifier = item.get(kind, {}).get("ids", {}).get("trakt")
                    if not isinstance(identifier, int) or isinstance(identifier, bool):
                        complete = False
                    else:
                        found.add(identifier)
                reason = "complete" if complete else "missing_identifiers"
    except Exception:
        reason = "read_failed"
        complete = False
    return {
        "media_type": media_type,
        "complete": complete,
        "reason": reason,
        "items": [
            {
                "id": identifier,
                "status": "watched"
                if identifier in found
                else "not_watched"
                if complete
                else "unknown",
            }
            for identifier in requested
        ],
    }


def register_membership_tool(mcp: FastMCP) -> None:
    @mcp.tool(
        name="check_watched",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    async def check_watched_tool(
        media_type: Literal["movies", "shows"],
        ids: Annotated[
            list[Annotated[int, Field(gt=0)]], Field(min_length=1, max_length=100)
        ],
    ) -> dict[str, Any]:
        """Check candidate Trakt IDs against watched history.

        Watched shows have at least one watched episode, not necessarily every episode.
        Unknown means unavailable data.
        """
        return await check_watched(get_client(UserClient), media_type, ids)
