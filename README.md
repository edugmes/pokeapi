# Index
### [1 - Overview](#1---overview-1)
### [2 - Running the project](#2---running-the-project-1)
### [3 - Project decisions](#3---project-decisions-1)


# 1 - Overview

Application directory structure:
```
.
├── Dockerfile          <-- Docker containers definition (Python and Redis)
├── README.md           <-- This file
├── docker-compose.yml  <-- Python image definition
├── project             <-- Source code folder
│   ├── __init__.py
│   ├── berry_api.py    <-- Functions to query PokeAPI endpoints and generate readable output
│   ├── main.py         <-- FastAPI app definition and endpoints
│   ├── schema.py       <-- Pydantic data schemas used for the endpoints output
│   ├── test_main.py    <-- Pytest test cases
│   └── utils.py        <-- Supportive methods (specially for berry_api.py)
└── requirements        <-- Pip dependencies of the Python image
    ├── base.txt        <-- libraries common for local and production environment
    ├── local.txt       <-- libraries only for local environment
    └── production.txt  <-- libraries only for production
```

# 2 - Running the project

Short version with three steps on the root folder (where `Dockerfile` is):
1. Run `docker build -t pokeapi/dev:1.0`
2. Copy the content of `.env_example` to a `.env` file
3. Run `docker-compose up -d`

Detailed version:
1. Install and run Docker
Installation steps [here](https://docs.docker.com/engine/install/).

2. Go to the root folder where `Dockerfile` and create the Python image to be used by the FastAPI container

On this step the proper dependencies are installed and folder structure is created. I'm using a multi-stage build
approach to optmize image size.

There are two types of image with differente package requirements. While the `dev` is focused on debug and compiling
stuff, the `prod` image is focused on light packages to reduce size.

Dev image
```
    docker build -t pokeapi/dev:v1.0 .
```
Prod image
```
    docker build --build-arg PROD=True -t pokeapi/prod:v1.0 .
```

3. Setup a .env file

In order to be closer to a production environment I've used Docker approach of environment variables
in a `.env` file. All sensitive data (e.g secret keys and db passwords) can be written to this file and are loaded only
at container startup, staying on the OS memory. For this security reason I've gitignored `.env`, so that this
data isn't exposed on the repository.

To run this project you must create one `.env` file on the same folder of `docker-compose.yml`. I've provided a
`.env_example` that you can simply copy-n-paste to your `.env` and you're ready to go.

For production environment this `.env` file should be stored in a safe cloud place (e.g. AWS services) or on the
systems runtime variables (e.g. Heroku works that way).

4. Run docker containers

Use the following command:
```
docker-compose up -d
```
It will read the containers defitions at `docker-compose.yml`, and start the fastAPI and Redis containers.

5. Go to your browser

Open [http://localhost:8000/allBerryStats](http://localhost:8000/allBerryStats) or
[http://localhost:8000/docs](http://localhost:8000/docs) on your browser and it should be working.

# 3 - Testing

To test `/allBerryStats` endpoint, use the following command on the terminal (outside the container):
```
docker exec web_c pytest -v
```

# 4 - Project decisions

## Problem approach

To generate the berries stats I've taken a four-step process:

1. Get basic information at [https://pokeapi.co/api/v2/berry/](https://pokeapi.co/api/v2/berry/).

2. With the basic information, determine how many berries (and endpoints) exists.

3. Retrieve every berry specific information using [https://pokeapi.co/api/v2/berry/{id}](https://pokeapi.co/api/v2/berry/{id})
where `id` ranges from 1 to the number of berries of `step 2`.

4. Clean the data retrieved and generate the stats.

## API exceptions handling
If the main berries information is not available for any reason, `/allBerryStats` endpoint throws an exception.

If the main information is available, but the application fails to retrieve specific information for all the berries,
`/allBerryStats` endpoint also throws an exception.

Otherwise the `/allBerryStats` endpoint returns valid data.

## Requests caching
Since the PokeAPI documentation 'suggests' users to avoid unecessary calls to their endpoints, I decided to
introduce a Redis container to cache `/allBerryStats` endpoint result, that way we avoid re-calculating everything
on every request.

The decorator `@cache(expire=15)` is in seconds and can be easily changed.

## Pandas
Thinking about generating stats for more endpoints and considering the PokeAPI key-value structure, I decided to
use `pandas` to compute statistics in a more standardized and efficient way.

## Testing
I wrote just one test case to validate `pytest`, but it definitely must be improved to include fixtures, and mockups,
specially for the async httpx requests.