import json
from typing import Union

import httpx


async def async_get(
    url: str, http_client: httpx.AsyncClient, params: dict = {}
) -> Union[dict, None]:
    """Make async API calls and return either None if API not available or a dictionary with valid data

    :param url: The API URL
    :param http_client: An httpx.AsyncClient object (optional)
    :param params: GET params for the request, defaults to {}
    :return: None if API unavailable, otherwise a dictionary with valid data
    """
    client = http_client if http_client != None else httpx.AsyncClient()

    try:
        response = await client.get(url)
        response.raise_for_status()
        return json.loads(response.text)
    # Request error handling (e.g. timeout)
    except httpx.RequestError as exc:
        return None
    # HTTP status code different than 2xx
    except httpx.HTTPStatusError as exc:
        return None


def sync_get(
    url: str, http_client: httpx.Client, params: dict = {}
) -> Union[dict, None]:
    """Make sync API calls and return either None if API not available or a dictionary with valid data

    :param url: The API URL
    :param http_client: An httpx.Client object (optional)
    :param params: GET params for the request, defaults to {}
    :return: None if API unavailable, otherwise a dictionary with valid data
    """
    client = http_client if http_client != None else httpx.Client()

    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        return json.loads(response.text)
    # Request error handling (e.g. timeout)
    except httpx.RequestError as exc:
        return None
    # HTTP status code different than 2xx
    except httpx.HTTPStatusError as exc:
        return None
