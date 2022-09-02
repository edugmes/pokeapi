import json
import os
from asyncio import gather
from typing import Dict, Union

import aioredis
import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """Setup redis connection to cache requests"""
    redis_addr = os.getenv("REDIS_URL")
    redis = aioredis.from_url(redis_addr, encoding="utf8", decode_responses=True)  # type: ignore

    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


async def async_get(
    url: str, http_client: httpx.AsyncClient, params: dict = {}
) -> Union[dict, None]:
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


async def berry_info(
    berry_id: int, http_client: httpx.AsyncClient
) -> Union[dict, None]:
    """Make a request to PokeAPI to get specific berry info

    :param berry_id: The ID of the be
    :param http_client: A httpx.Client object to use for the request
    :return: A dictionary with the berry info
    """
    url = f"https://pokeapi.co/api/v2/berry/{berry_id}/"

    data = await async_get(url, http_client)

    return data


def berries_basic_info(offset: int = 0, limit: int = 1) -> Union[dict, None]:
    """Make a request to PokeAPI to get basic berries info

    :param offset: The offset from which the data is returned, defaults to 0
    :param limit: The number of results to return, defaults to 1
    :return: A dictionary with the list of berries API information
    """
    url = "https://pokeapi.co/api/v2/berry/"
    params = {"offset": offset, "limit": limit}

    client = httpx.Client()

    data = sync_get(url, client, params=params)

    return data


def berries_count(berries_general_info: dict) -> int:
    """Take a berries dictionary with general info and returns the number of berries

    :param berries_general_info: The dictionary with berries general info
    :return: Number of berries
    """
    return berries_general_info["count"]


async def berries_specific_info(count: int) -> list:
    """Create a list of async `berry_info` tasks, and then waits for all of them to return berries specific info

    :param count: The number of berries to get info for
    :return: A list of dictionaries with berries specific info
    """
    result = []

    async with httpx.AsyncClient() as http_client:
        berries = [
            berry_info(berry_id, http_client) for berry_id in range(1, count + 1)
        ]
        result = await gather(*berries)

    # Clean up berries data that failed to be retrieved
    result = list(filter(lambda res: res != None, result))

    return result


def filter_specific_info(specific_info: list, filter: list = []) -> pd.DataFrame:
    """Given a list of dictionaries of berries specific data, return a dataframe with the columns specified in the filter list

    :param specific_info: list of dictionaries of berries specific data
    :param filter: filter list to generate the dataframe columns
    :return: A dataframe with the columns specified in the filter list.
    """
    cols = filter
    data = []

    for info in specific_info:
        filtered_data = [info[col] for col in cols]
        data.append(filtered_data)

    df = pd.DataFrame(data=data, columns=cols)

    return df


def berries_stats(berries_df: pd.DataFrame) -> dict:
    """Generate growth time stats for berries

    :param berries_df: A pandas dataframe with the berries names and growth time
    :return: A dictionary with berries names and growth stats (min, max, median, variance, mean, and frequency)
    """
    names = berries_df["name"].tolist()
    min_value = int(berries_df["growth_time"].min())
    median_value = round(float(berries_df["growth_time"].median()), 2)
    max_value = int(berries_df["growth_time"].max())
    variance_value = round(float(berries_df["growth_time"].var()), 2)  # type: ignore
    mean_value = round(float(berries_df["growth_time"].mean()), 2)
    frequency = berries_df["growth_time"].value_counts().to_dict()

    return {
        "berries_names": names,
        "min_growth_time": min_value,
        "median_growth_time": median_value,
        "max_growth_time": max_value,
        "variance_growth_time": variance_value,
        "mean_growth_time": mean_value,
        "frequency_growth_time": frequency,
    }


@app.get("/allBerryStats")
@cache(expire=15)
async def all_berry_stats() -> dict:
    """Get berries names and growth time stats (min, max, median, variance, mean, and frequency)

    :raises HTTPException: If either PokeAPI general infor or all the berries specific info can't be retrieved
    :return: The berries stats
    """
    basic_info = berries_basic_info()

    # Check if basic info could be retrieved
    if not basic_info:
        raise HTTPException(
            status_code=404, detail="PokeAPI not available at the moment"
        )

    count_info = berries_count(basic_info)
    specific_info = await berries_specific_info(count_info)

    df = filter_specific_info(specific_info, filter=["name", "growth_time"])

    # Check if at least one berry specific info could be retrieved
    if len(df.index) == 0:
        raise HTTPException(
            status_code=404, detail="PokeAPI not available at the moment"
        )

    stats = berries_stats(df)

    return stats
