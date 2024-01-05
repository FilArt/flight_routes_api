import random

from geoalchemy2 import Geography
from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

metadata = MetaData()

airlines = Table(
    "airlines",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String),
)

aircrafts = Table(
    "aircrafts",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String),
)

waypoints = Table(
    "waypoints",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String),
    Column("geom", Geography(geometry_type="POINT", srid=4326)),
)

edges = Table(
    "edges",
    metadata,
    Column("name", String, primary_key=True),
    Column("source", Integer, ForeignKey("waypoints.id")),
    Column("target", Integer, ForeignKey("waypoints.id")),
    Column("cost", Float, default=lambda _: random.random()),
    # eet, mach...
)

flights = Table(
    "flights",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("airline_id", ForeignKey(airlines.c.id)),
    Column("aircraft_id", ForeignKey(aircrafts.c.id)),
    Column("departure", ForeignKey(waypoints.c.id)),
    Column("arrival", ForeignKey(waypoints.c.id)),
    Column("departure_time", DateTime),
    Column("arrival_time", DateTime),
    Column("fuel_consumption", Float),
    Column("fpl", ARRAY(Integer)),
)
