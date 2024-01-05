from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AirlineBase(BaseModel):
    name: str


class AirlineCreate(AirlineBase):
    pass


class Airline(AirlineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AirportBase(BaseModel):
    name: str


class AirportCreate(AirportBase):
    pass


class Airport(AirportBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class FlightBase(BaseModel):
    departure: int
    arrival: int
    airline_id: int
    aircraft_id: int
    fuel_consumption: float
    departure_time: datetime
    arrival_time: datetime
    fpl: list[int]


class FlightCreate(FlightBase):
    pass


class Flight(FlightBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class FlightRoute(BaseModel):
    fpl: list[str]


class AlternativeRoute(FlightRoute):
    fuel_savings: float
    time_savings: str


class NodeBase(BaseModel):
    pass


class NodeCreate(NodeBase):
    pass


class Node(NodeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class Edge(BaseModel):
    source: Node
    target: Node
    cost: float
