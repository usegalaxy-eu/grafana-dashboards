"""Retrieve publicly available dashboards from a Grafana instance.

Fetch publicly available dashboards from a Grafana instance via API calls and
save them to JSON files.

- `sys.argv[1]`: URL of the Grafana instance to retrieve Dashboards from.
- `sys.argv[2]`: Directory to save dashboard JSON files to.

Dashboards are retrieved and saved concurrently using `aiohttp` and `aiofiles`.
"""

import asyncio
import json
import sys
from typing import AsyncIterator

import aiofiles
import aiohttp


AIOHTTP_MAX_CONCURRENT_REQUESTS: int = 50


async def list_dashboards(
    grafana_url: str,
    session: aiohttp.ClientSession,
) -> AsyncIterator[str]:
    """Retrieve list of dashboards from search endpoint.

    References:
      - [1] https://grafana.com/docs/grafana/latest/developers/http_api/folder_dashboard_search/  # noqa
    """
    limit = AIOHTTP_MAX_CONCURRENT_REQUESTS - 1
    page = 1
    more_pages = True

    while more_pages:
        async with session.get(
            f"{grafana_url}/api/search?limit={limit}?page={page}?query=&",
            headers={"Content-Type": "application/json"},
        ) as response:
            response_json = await response.json()
            for dashboard in (
                item for item in response_json if item.get("type") == "dash-db"
            ):
                yield dashboard

        if len(response_json) < limit:
            more_pages = False
        else:
            page += 1


async def save_dashboard_json(
    uid: str, grafana_url: str, path: str, session: aiohttp.ClientSession
) -> str:
    """Retrieve a dashboard by uid and save it to a JSON file."""
    async with session.get(
        f"{grafana_url}/api/dashboards/uid/{uid}",
        headers={"Content-Type": "application/json"},
    ) as response:
        dashboard_json = await response.json()
        metadata = dashboard_json["dashboard"]

        file_name = f"{metadata.get('title') or metadata.get('uid')}.json"
        # forward slashes are not allowed in UNIX paths
        file_name = file_name.replace("/", "⁄")
        # NULL bytes are not allowed in UNIX paths
        file_name = file_name.replace("\x00", "\u200B")
        # `.` and `..` are reserved names
        if file_name == ".":
            file_name = "∘"
        elif file_name == "..":
            file_name = "∘∘"

        async with aiofiles.open(f"{path}/{file_name}", "w") as file:
            json_string = json.dumps(dashboard_json, indent=2)
            await file.write(json_string)


async def main(grafana_url: str, path: str):
    """Retrieve and save publicly available dashboards from a Grafana instance."""
    connector = aiohttp.TCPConnector(limit=AIOHTTP_MAX_CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            asyncio.create_task(
                save_dashboard_json(
                    dashboard["uid"],
                    grafana_url,
                    path,
                    session,
                )
            )
            async for dashboard in list_dashboards(grafana_url, session)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    grafana_url, path = sys.argv[1:]
    asyncio.run(main(grafana_url, path))
