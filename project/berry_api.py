from asyncio import gather
from typing import Union

import httpx
import pandas as pd

from utils import async_get, sync_get


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
