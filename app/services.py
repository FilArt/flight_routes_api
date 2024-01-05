import heapq
import itertools
from datetime import timedelta

from databases import Database
from fastapi import Depends
from fastapi.exceptions import HTTPException

from app.deps import get_db

from .models import flights, waypoints
from .schemas import Edge, Flight, FlightCreate, Node


class FlightService:
    def __init__(self, db: Database = Depends(get_db)):
        self.db = db

    async def create_flight(self, flight_data: FlightCreate) -> Flight:
        flight = flight_data.model_dump()
        query = flights.insert()
        created_id = await self.db.execute(query, values=flight)
        return {**flight, "id": created_id}

    async def get_most_used_route(
        self,
        departure,
        arrival,
        airline_id=None,
        aircraft_id=None,
        start_date=None,
        end_date=None,
    ):
        where, values = self._get_where(
            departure,
            arrival,
            airline_id,
            aircraft_id,
            start_date,
            end_date,
        )

        query = f"""
            SELECT fpl, COUNT(*) as usage_count
            FROM flights
            WHERE {where}
            GROUP BY fpl
            ORDER BY usage_count DESC
            LIMIT 1;
        """
        result = await self.db.fetch_one(query, values=values)
        if not result:
            raise HTTPException(404)
        return {
            **result,
            "fpl": [wp.name for wp in await self.get_waypoints(result["fpl"])],
        }

    async def get_most_efficient(
        self,
        departure,
        arrival,
        by_time=True,
        by_fuel=False,
    ):
        where, values = self._get_where(departure, arrival)

        select_time = "RANK() OVER(ORDER BY AVG(EXTRACT(EPOCH FROM (flights.arrival_time - flights.departure_time)))) AS score"
        select_fuel = "RANK() OVER(ORDER BY AVG(flights.fuel_consumption)) AS score"
        query = f"""
            SELECT fpl, {select_time if by_time else select_fuel}
            FROM flights
            WHERE {where}
            GROUP BY fpl
            ORDER BY score ASC LIMIT 1
        """
        result = await self.db.fetch_one(query, values=values)
        if not result:
            raise HTTPException(404)
        return {
            **result,
            "fpl": [wp.name for wp in await self.get_waypoints(result["fpl"])],
        }

    async def get_alternatives(self, flight_id: int):
        flight = await self.db.fetch_one(
            flights.select().where(flights.c.id == flight_id)
        )
        if not flight:
            return []

        flight = Flight(**flight[0])
        where, values = self._get_where(flight.departure, flight.arrival)
        where = f"{where} AND flights.id != :flight_id"

        values["flight"] = flight_id
        values["current_arrival"] = flight.arrival_time
        values["current_fuel_consumption"] = flight.fuel_consumption

        query = f"""
        SELECT
            edges.id, edges.path,
            AVG(EXTRACT(EPOCH FROM(:current_arrival - flights.arrival_time))) AS time_savings,
            AVG(:current_fuel_consumption - flights.fuel_consumption) AS fuel_savings
        FROM
            edges
        JOIN
            flights ON edges.source_id = flights.departure AND edges.target_id = flights.arrival
        WHERE
            {where}
        GROUP BY
            edges.id;
        """
        result = await self.db.fetch_all(query, values=values)
        return [
            {
                "id": i.id,
                "path": i.path,
                "time_savings": str(timedelta(seconds=int(i.time_savings))),
                "fuel_savings": int(i.fuel_savings),
            }
            for i in result
        ]

    async def get_shortest_route(self, departure: Node, arrival: Node):
        all_waypoints: list[Node] = await self.db.fetch_all(waypoints)

        def calculate_distance(node1: Node, node2: Node) -> float:
            return geopy.distance.distance(
                (node1.lat, node1.lon), (node2.lat, node2.lon)
            ).km

        edges = []
        for source, target in itertools.permutations(all_waypoints, 2):
            cost = calculate_distance(source, target)
            edges.append(Edge(source, target, cost))

        def get_neighbors(node: Node):
            neighbors = []
            for edge in edges:
                if edge.source == node:
                    neighbors.append(edge)
            return neighbors

        # use Dijkstra's algorithm
        distances = {departure.id: 0}
        priority_queue = [(0, departure.id)]
        previous_nodes = {}
        visited = set()

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)

            if current_node == arrival.id:
                path = []
                while current_node in previous_nodes:
                    path.insert(0, current_node)
                    current_node = previous_nodes[current_node]
                return [departure.id] + path

            if current_node in visited:
                continue

            visited.add(current_node)
            for edge in get_neighbors(current_node):
                neighbor = edge.target.id
                distance = current_distance + edge.cost
                if neighbor not in distances or distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))

        return []

    def _get_where(
        self,
        departure,
        arrival,
        airline_id=None,
        aircraft_id=None,
        start_date=None,
        end_date=None,
    ):
        values = {
            "departure": departure,
            "arrival": arrival,
        }
        where = "flights.departure = :departure \
            AND flights.arrival = :arrival"
        if airline_id:
            values["airline_id"] = airline_id
            where += " AND flights.airline_id = :airline_id "
        if aircraft_id:
            values["aircraft_id"] = aircraft_id
            where += " AND flights.aircraft_id = :aircraft_id "
        if start_date:
            values["start_date"] = start_date
            where += " AND flights.departure_time >= :start_date "
        if end_date:
            values["end_date"] = end_date
            where += " AND flights.departure_time <= :end_date "
        return where, values

    async def get_waypoints(self, fpl: list[int]):
        query = waypoints.select().where(waypoints.c.id.in_(fpl))
        wps = {wp.id: wp for wp in await self.db.fetch_all(query)}
        return [wps[i] for i in fpl]
