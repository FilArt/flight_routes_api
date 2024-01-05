from datetime import datetime

from fastapi import APIRouter, Depends, Query

from .schemas import (
    AlternativeRoute,
    Flight,
    FlightCreate,
    MostEfficientRoute,
    MostUsedRoute,
)
from .services import FlightService

router = APIRouter()


@router.post("/flights/routes", response_model=Flight)
async def create_flight(
    flight: FlightCreate,
    service: FlightService = Depends(FlightService),
):
    return await service.create_flight(flight)


@router.get("/flights/most_used", response_model=MostUsedRoute)
async def get_most_used_flight_route(
    departure: int,
    arrival: int,
    airline_id: int | None = None,
    aircraft_id: int | None = None,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    service: FlightService = Depends(FlightService),
):
    return await service.get_most_used_route(
        departure,
        arrival,
        airline_id,
        aircraft_id,
        start_date,
        end_date,
    )


@router.get("/flights/most_efficient", response_model=MostEfficientRoute)
async def get_most_efficient_flight_route(
    departure: int,
    arrival: int,
    by_time: bool = False,
    by_fuel: bool = False,
    service: FlightService = Depends(FlightService),
):
    return await service.get_most_efficient(
        departure,
        arrival,
        by_time,
        by_fuel,
    )


@router.get("/flights/alternatives", response_model=list[AlternativeRoute])
async def get_alternative_route(
    flight_id: int, service: FlightService = Depends(FlightService)
):
    return await service.get_alternatives(flight_id)


# TODO
# @router.get("/flights/shortest")
