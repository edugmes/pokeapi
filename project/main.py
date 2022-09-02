import os

import aioredis
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from berry_api import (
    berries_basic_info,
    berries_count,
    berries_specific_info,
    berries_stats,
    filter_specific_info,
)
from schema import BerriesStatsOut, UnavailablePokeAPI

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """Setup redis connection to cache requests"""
    redis_addr = os.getenv("REDIS_URL")
    redis = aioredis.from_url(redis_addr, encoding="utf8", decode_responses=True)  # type: ignore

    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.get(
    "/allBerryStats",
    response_model=BerriesStatsOut,
    responses={404: {"model": UnavailablePokeAPI}},
)
@cache(expire=15)
async def all_berry_stats() -> dict:
    """Get berries names and growth time stats (min, max, median, variance, mean, and frequency)

    :raises HTTPException: If either PokeAPI general info or all the berries specific info can't be retrieved
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
