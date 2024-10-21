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
from collections import defaultdict
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
            f"{grafana_url}/api/search?limit={limit}&page={page}&query=",
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
) -> dict:
    """Retrieve a dashboard by uid and save it to a JSON file."""
    async with session.get(
        f"{grafana_url}/api/dashboards/uid/{uid}",
        headers={"Content-Type": "application/json"},
    ) as response:
        dashboard_json = await response.json()
        metadata = dashboard_json["dashboard"]

        file_name = f"{metadata.get('title') or metadata['uid']}.json"

        async with aiofiles.open(f"{path}/{file_name}", "w") as file:
            json_string = json.dumps(dashboard_json, indent=2)
            await file.write(json_string)

    return metadata | {"file_name": file_name}


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
        metadata = await asyncio.gather(*tasks)

    # ensure all dashboards are saved to different files
    file_names_to_metadata = defaultdict(list)
    for meta in metadata:
        file_names_to_metadata[meta["file_name"]] += [meta]
    try:
        assert len(file_names_to_metadata) == sum(
            len(dashboards_metadata)
            for dashboards_metadata in file_names_to_metadata.values()
        )
    except AssertionError as exception:
        error_text = (
            "Two or more dashboards have the same file name assigned, "
            "aborting... Please rename some of the following dashboards:\n"
        )
        repeated_file_names = (
            file_name
            for file_name, dashboards_metadata in (
                file_names_to_metadata.items()
            )
            if len(dashboards_metadata) >= 2
        )
        for file_name in repeated_file_names:
            for meta in file_names_to_metadata[file_name]:
                title = meta.get("title")
                uid = meta["uid"]
                error_text += f"- "
                error_text += f"name: {title}, " if title else ""
                error_text += f"uid: {uid}, "
                error_text = error_text[:-2] + "\n"
        raise AssertionError(error_text) from exception


if __name__ == "__main__":
    grafana_url, path = sys.argv[1:]
    asyncio.run(main(grafana_url, path))
