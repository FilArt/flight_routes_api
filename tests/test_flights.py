import json
from datetime import datetime, timedelta

import pytest
from databases import Database
from httpx import AsyncClient

from app.models import aircrafts, airlines, flights, waypoints


@pytest.fixture
def create_airline(db: Database):
    async def _(name="Test Airline"):
        query = airlines.insert().values(name=name)
        created_id = await db.execute(query)
        return created_id

    return _


@pytest.fixture
def create_aircraft(db: Database):
    async def _(name: str = "Test Aircraft"):
        query = aircrafts.insert().values(name=name)
        return await db.execute(query)

    return _


@pytest.fixture
def create_waypoint(db: Database):
    async def _(name="Test Airport"):
        query = waypoints.insert().values(name=name)
        return await db.execute(query)

    return _


@pytest.fixture
def create_flight(
    create_waypoint,
    create_airline,
    create_aircraft,
    db: Database,
):
    async def _(
        departure=None,
        arrival=None,
        airline=None,
        aircraft=None,
        fpl=None,
        fuel_consumption=500,
        departure_time=datetime.now(),
        arrival_time=datetime.now(),
    ):
        if airline is None:
            airline = await create_airline()
        if aircraft is None:
            aircraft = await create_aircraft()
        if departure is None:
            departure = await create_waypoint(name="departure")
        if arrival is None:
            arrival = await create_waypoint(name="arrival")
        if fpl is None:
            fpl = [departure, arrival]

        values = dict(
            fpl=fpl,
            departure=departure,
            arrival=arrival,
            airline_id=airline,
            aircraft_id=aircraft,
            fuel_consumption=fuel_consumption,
            departure_time=departure_time,
            arrival_time=arrival_time,
        )
        query = flights.insert()
        created_id = await db.execute(query, values=values)
        return created_id

    return _


@pytest.fixture
async def gen_flight(create_flight):
    async def _(
        departure=None,
        arrival=None,
        fuel_consumption: float = 1000.0,
        duration: timedelta = timedelta(hours=1),
        fpl=None,
    ):
        departure_time = datetime(2024, 1, 5, 14, 30, 0)
        await create_flight(
            fpl=fpl,
            departure=departure,
            arrival=arrival,
            fuel_consumption=fuel_consumption,
            departure_time=departure_time,
            arrival_time=departure_time + duration,
        )

    return _


async def test_create_flight(
    client: AsyncClient,
    create_waypoint,
    create_airline,
    create_aircraft,
):
    airport1 = await create_waypoint(name="wp1")
    airport2 = await create_waypoint(name="wp2")
    airline = await create_airline()
    aircraft = await create_aircraft()

    data = {
        "fpl": [airport1, airport2],
        "airline_id": airline,
        "aircraft_id": aircraft,
        "fuel_consumption": 500,
        "departure": airport1,
        "arrival": airport2,
        "departure_time": "2024-01-05T14:30:00",
        "arrival_time": "2024-01-05T15:30:00",
    }
    response = await client.post("/flights/routes", json=data)
    assert response.status_code == 200, response.json()

    for k, v in response.json().items():
        if k == "id":
            assert v
        elif k == "fpl":
            data[k] == ["wp1", "wp2"]
        else:
            assert data[k] == v


async def test_get_most_used_flight_routes(
    client: AsyncClient, gen_flight, create_waypoint
):
    departure, wp, arrival = (
        await create_waypoint("dep"),
        await create_waypoint("wp"),
        await create_waypoint("arr"),
    )
    fpl = [departure, wp, arrival]
    defaults = dict(departure=departure, arrival=arrival)

    # same route, 2 usage
    await gen_flight(**defaults, fpl=fpl)
    await gen_flight(**defaults, fpl=fpl)
    await gen_flight(**defaults)  # new route, 1 usage

    params = {"departure": departure, "arrival": arrival}
    response = await client.get("/flights/most_used", params=params)
    result = response.json()

    assert response.status_code == 200
    assert result["fpl"] == ["dep", "wp", "arr"]


@pytest.mark.parametrize(
    ["by_time", "by_fuel"],
    [(True, False), (False, True)],
)
async def test_get_most_efficient_flight_route(
    client: AsyncClient,
    gen_flight,
    create_waypoint,
    by_time,
    by_fuel,
):
    departure, arrival = await create_waypoint("dep"), await create_waypoint("arr")
    default = dict(departure=departure, arrival=arrival)
    await gen_flight(
        **default,
        fpl=[departure, await create_waypoint(name="best_time"), arrival],
        duration=timedelta(minutes=30),
    )
    await gen_flight(
        **default,
        fpl=[departure, await create_waypoint(name="best_fuel"), arrival],
        fuel_consumption=500,
    )
    params = {
        "departure": departure,
        "arrival": arrival,
        "by_time": by_time,
        "by_fuel": by_fuel,
    }
    response = await client.get("/flights/most_efficient", params=params)
    result = response.json()
    fpl = result["fpl"]
    if by_time:
        assert fpl[1] == "best_time", result
    elif by_fuel:
        assert fpl[1] == "best_fuel"


# async def test_get_alternative_route(
#     client: AsyncClient, create_waypoint, gen_flight, create_flight
# ):
#     departure, arrival = await create_waypoint("dep"), await create_waypoint("arr")
#     route1, route2, route3 = (
#         await create_flight(fpl=[departure, arrival]),
#         await create_flight(fpl=[departure, await create_waypoint("alt1"), arrival]),
#         await create_flight(fpl=[departure, await create_waypoint("alt2"), arrival]),
#     )
#     default = dict(departure=departure, arrival=arrival)
#     await gen_flight(fpl=route1, **default)
#     await gen_flight(fpl=route2, **default, duration=timedelta(minutes=30))
#     await gen_flight(fpl=route3, **default, fuel_consumption=500)
#     response = await client.get(f"/flights/alternatives?flightroute_id_id={route1}")
#     result = response.json()
#     assert len(result) == 2
#     assert result[0]["id"] == route2
#     assert result[0]["time_savings"] == "0:30:00"
#     assert result[1]["id"] == route3
#     assert result[1]["fuel_savings"] == 500


# async def test_get_shortest_route(client: AsyncClient, db):
#     with open("sample_tech_test.json") as f:
#         data = json.loads(f.read())

#     sample_waypoints = [
#         {
#             "name": waypoint["name"],
#             "latitude": waypoint["latitude"],
#             "longitude": waypoint["longitude"],
#         }
#         for waypoint in data["lastOfp"]["waypoints"]
#     ]

#     query = waypoints.insert().values(sample_waypoints)
#     created_id = await db.execute(query)
#     assert created_id
