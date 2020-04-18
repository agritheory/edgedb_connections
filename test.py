import typing
import pytest
import edgedb
from connect import EdgeDBConnection


@pytest.fixture(scope="module")
def connection_object() -> EdgeDBConnection:
    return EdgeDBConnection(
        dsn=None,
        host="localhost",
        port=5656,
        admin=False,
        user="edgedb",
        password="edgedb",
        database="edgedb",
        timeout=60,
    )


@pytest.mark.usefixtures("connection_object")
def test_connection_object(connection_object) -> None:
    assert connection_object.host == "localhost"
    assert connection_object.port == 5656
    assert connection_object.admin is False
    assert connection_object.timeout == 60
    assert connection_object.user == "edgedb"
    assert connection_object.password == "edgedb"
    assert connection_object.database == "edgedb"


@pytest.mark.usefixtures("connection_object")
def test_edgedb_sync_connection(connection_object) -> None:
    sync_connection = connection_object("SYNC")
    assert isinstance(sync_connection, edgedb.BlockingIOConnection)
    sync_connection.close()
    assert sync_connection.is_closed() is True


@pytest.mark.usefixtures("connection_object")
@pytest.mark.asyncio
async def test_edgedb_async_connections(connection_object) -> None:
    async_connection = await connection_object("ASYNC")
    assert isinstance(async_connection, edgedb.AsyncIOConnection)
    await async_connection.aclose()
    assert async_connection.is_closed() is True


@pytest.mark.usefixtures("connection_object")
@pytest.mark.asyncio
async def test_edgedb_async_pool(connection_object) -> None:
    async_pool = await connection_object("POOL")
    assert isinstance(async_pool, edgedb.AsyncIOConnection)
    await async_pool.aclose()


@pytest.mark.usefixtures("connection_object")
@pytest.mark.xfail
def test_edgedb_enum_validator(connection_object) -> typing.NoReturn:
    sync_connection = connection_object("sync")
