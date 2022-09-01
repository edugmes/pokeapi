import json
import os
from asyncio import gather

import aioredis
import httpx
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """Setup redis connection to cache requests
    """
    redis_addr = os.getenv("REDIS_URL")
    redis =  aioredis.from_url(redis_addr, encoding="utf8", decode_responses=True)

    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


async def berry_info(berry_id: int, http_client: httpx.AsyncClient) -> dict:
    """Make a request to PokeAPI to get specific berry info

    :param berry_id: The ID of the be
    :param http_client: A httpx.Client object to use for the request
    :return: A dictionary with the berry info
    """
    url = f'https://pokeapi.co/api/v2/berry/{berry_id}/'

    response = await http_client.get(url)

    json_response = json.loads(response.text)

    return json_response


def berries_basic_info(offset: int = 0, limit: int = 1) -> dict:
    """Make a request to PokeAPI to get basic berries info

    :param offset: The offset from which the data is returned, defaults to 0
    :param limit: The number of results to return, defaults to 1
    :return: A dictionary with the list of berries API information
    """
    url = 'https://pokeapi.co/api/v2/berry/'
    params = {'offset': offset, 'limit': limit}

    client = httpx.Client()

    response = client.get(url, params=params)
    data = json.loads(response.text)

    return data


def berries_count(berries_general_info: dict) -> int:
    """Take a berries dictionary with general info and returns the number of berries

    :param berries_general_info: The dictionary with berries general info
    :return: Number of berries
    """
    return berries_general_info['count']


async def berries_specific_info(count: int) -> list:
    """Create a list of async `berry_info` tasks, and then waits for all of them to return berries specific info

    :param count: The number of berries to get info for
    :return: A list of dictionaries with berries specific info
    """
    result = []

    async with httpx.AsyncClient() as http_client:
        berries = [berry_info(berry_id, http_client) for berry_id in range(1, count+1)]
        result = await gather(*berries)

    return result


@app.get("/")
@cache(expire=60)
async def read_root():
    basic_info = berries_basic_info()
    count_info = berries_count(basic_info)
    specific_info = await berries_specific_info(10)

    return {"berries_count": count_info, 'berries_basic_info': basic_info, 'berries_specific_info': specific_info}
