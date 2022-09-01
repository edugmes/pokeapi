import json

import httpx
from fastapi import FastAPI

app = FastAPI()

def berry_info(berry_id: int, http_client: httpx.Client) -> dict:
    """Make a request to PokeAPI to get specific berry info

    :param berry_id: The ID of the be
    :param http_client: A httpx.Client object to use for the request
    :return: A dictionary with the berry info
    """
    url = f'https://pokeapi.co/api/v2/berry/{berry_id}/'

    response = http_client.get(url)

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


@app.get("/")
def read_root():
    client = httpx.Client()
    data = berries_basic_info()
    return {"berries_count": berries_count(data), 'berries_data': data, 'berry_1_info': berry_info(1, client)}
