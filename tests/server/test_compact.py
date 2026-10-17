import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from models.formatters.search import SearchFormatters
from server.search.tools import register_search_tools
from server.user.compact import check_watched, compact_items, register_membership_tool
from server.user.tools import register_user_tools


def test_compact_keeps_ids_and_explicit_truncation():
    items = [
        {
            "movie": {
                "title": "Film",
                "year": 2020,
                "ids": {"trakt": 10},
                "overview": "Long plot " * 100,
            },
            "plays": 1,
        }
    ]
    result = json.loads(compact_items(items, "movie", total=200))
    assert result == {
        "items": [{"id": 10, "title": "Film", "year": 2020, "plays": 1}],
        "returned": 1,
        "total": 200,
        "truncated": True,
    }
    detailed = SearchFormatters.format_movie_search_results(items)
    assert "Long plot" in detailed
    assert "Use this ID for comments" not in detailed


@pytest.mark.asyncio
async def test_membership_checks_full_list_without_display_cap():
    client = AsyncMock()
    client.ensure_authenticated.return_value = True
    client.get_user_watched_movies.return_value = [
        {"movie": {"ids": {"trakt": identifier}}} for identifier in range(1, 251)
    ]
    result = await check_watched(client, "movies", [250, 999, 250])
    assert result["complete"] is True
    assert result["items"] == [
        {"id": 250, "status": "watched"},
        {"id": 999, "status": "not_watched"},
    ]


@pytest.mark.asyncio
async def test_missing_ids_and_auth_failures_are_not_absence():
    client = AsyncMock()
    client.ensure_authenticated.return_value = True
    client.get_user_watched_shows.return_value = [{"show": {"ids": {}}}]
    result = await check_watched(client, "shows", [1])
    assert result["items"][0]["status"] == "unknown"
    client.get_user_watched_shows.side_effect = RuntimeError("secret fixture")
    result = await check_watched(client, "shows", [1])
    assert "secret" not in str(result)
    assert result["complete"] is False
    client.ensure_authenticated.return_value = False
    result = await check_watched(client, "shows", [1])
    assert result["reason"] == "not_authenticated"


@pytest.mark.asyncio
async def test_mcp_default_compact_and_detailed_escape_hatch():
    server = FastMCP("test")
    register_user_tools(server)
    register_search_tools(server)
    register_membership_tool(server)
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert (
        tools["search_movies"].inputSchema["properties"]["detail"]["default"]
        == "compact"
    )
    assert tools["check_watched"].annotations.readOnlyHint is True
    fixture = [
        {
            "movie": {
                "ids": {"trakt": 1},
                "title": "Film",
                "year": 2020,
                "overview": "Full plot",
            }
        }
    ]
    client = AsyncMock()
    client.ensure_authenticated.return_value = True
    client.get_user_watched_movies.return_value = fixture
    with patch("server.user.tools.get_client", return_value=client):
        small = await server.call_tool("fetch_user_watched_movies", {})
        full = await server.call_tool(
            "fetch_user_watched_movies", {"detail": "detailed"}
        )
    # FastMCP may return content alone or a (content, structured) pair.
    small_content = small[0] if isinstance(small, tuple) else small
    full_content = full[0] if isinstance(full, tuple) else full
    assert json.loads(small_content[0].text)["items"][0]["id"] == 1
    assert "Full plot" not in small_content[0].text
    assert "Full plot" in full_content[0].text
