import asyncio
import datetime
import typing as t

import aiohttp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .database import DataPoint, datapoint_table


async def get_data_points(
    server: str, api_key: t.Optional[str], http: aiohttp.ClientSession
) -> t.List[DataPoint]:
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.0/sensors/"
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key
    async with http.get(url, headers=headers) as request:
        result = await request.json()
        ok = request.status == 200
    now = datetime.datetime.now()
    if ok:
        points = []
        for value in result["sensors"]:
            points.append(
                DataPoint(
                    sensor_name=value["id"], collected_at=now, data=value["value"]
                )
            )
        return points
    else:
        raise ValueError(
            f"Error loading data from {server}: " + result.get("error", "Unknown")
        )


def handle_result(result: t.List[DataPoint], session: Session) -> t.List[DataPoint]:
    for point in result:
        insert = datapoint_table.insert().values(**point._asdict())
        sql_result = session.execute(insert)
        point.id = sql_result.inserted_primary_key[0]
    return result


async def add_data_from_sensors(
    session: Session, servers: t.Tuple[str], api_key: t.Optional[str]
) -> t.List[DataPoint]:
    tasks: t.List[t.Awaitable[t.List[DataPoint]]] = []
    points: t.List[DataPoint] = []
    async with aiohttp.ClientSession() as http:
        tasks = [get_data_points(server, api_key, http) for server in servers]
        for results in await asyncio.gather(*tasks):
            points += results
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, handle_result, points, session)
    return points


def standalone(
    db_uri: str, servers: t.Tuple[str], api_key: t.Optional[str], echo: bool = False
) -> None:
    engine = create_engine(db_uri, echo=echo)
    sm = sessionmaker(engine)
    Session = sm()
    asyncio.run(add_data_from_sensors(Session, servers, api_key))
    Session.commit()


if __name__ == "__main__":
    standalone(
        db_uri="postgresql+psycopg2://apd@localhost/apd",
        servers=("http://pvoutput:8080/",),
        api_key="h3hdfjksfhwkjehnwekj",
    )
