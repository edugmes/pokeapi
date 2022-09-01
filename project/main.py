import json

import httpx
from fastapi import FastAPI

app = FastAPI()

def berries_basic_info(offset: int = 0, limit: int = 1) -> dict:
    url = 'https://pokeapi.co/api/v2/berry/'
    params = {'offset': offset, 'limit': limit}

    client = httpx.Client()

    response = client.get(url, params=params)
    data = json.loads(response.text)

    return data

def berries_count(berries_general_info: dict) -> int:
    return berries_general_info['count']


@app.get("/")
def read_root():
    data = berries_basic_info()
    return {"berries_count": berries_count(data), 'berries_data': data}
