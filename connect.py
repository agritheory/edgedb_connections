from __future__ import annotations

import typing
from enum import Enum, auto
from dataclasses import dataclass

import edgedb


CONNECTION_TYPES = ('SYNC', 'ASYNC', 'POOL')


@dataclass
class EdgeDBConnection:
    dsn: typing.Optional[str] = None
    host: typing.Optional[str] = None
    port: int = 5656
    admin: typing.Optional[bool] = False
    user: typing.Optional[str] = None
    password: typing.Optional[str] = None
    database: typing.Optional[str] = None
    timeout: int = 60
    pool: typing.Optional[edgedb.AsyncIOPool] = None
    pool_min_size: int = 1
    pool_max_size: int = 1
    connection_type: ConnectionType = None

    def __call__(
        self, connection_type: ConnectionType = None
    ) -> typing.Union[
        edgedb.BlockingIOConnection,
        typing.Coroutine[typing.Any, typing.Any, edgedb.AsyncIOConnection],
    ]:
        if not connection_type:
            connection_type = self.connection_type
        if connection_type not in CONNECTION_TYPES:
            raise TypeError(
                f"'connection_type' must be one of 'SYNC', 'ASYNC' or 'POOL'. \
                You provided '{connection_type}'"
            )
        if connection_type == "ASYNC":
            return self.connect_async()
        elif connection_type == "SYNC":
            return self.connect_sync()
        elif connection_type == "POOL":
            return self.connect_async_pool()

    def connect_sync(
        self,
        connection: typing.Optional[EdgeDBConnection] = None,
    ) -> edgedb.BlockingIOConnection:
        return edgedb.connect(
            dsn=self.dsn,
            host=self.host,
            port=self.port,
            admin=bool(self.admin),
            user=self.user,
            password=self.password,
            database=self.database,
            timeout=self.timeout,
        )

    async def connect_async(
        self,
        connection: typing.Optional[EdgeDBConnection] = None,
    ) -> edgedb.AsyncIOConnection:
        return await edgedb.async_connect(
            dsn=self.dsn,
            host=self.host,
            port=self.port,
            admin=bool(self.admin),
            user=self.user,
            password=self.password,
            database=self.database,
            timeout=self.timeout,
        )

    async def connect_async_pool(
        self,
        connection: typing.Optional[EdgeDBConnection] = None,
    ) -> edgedb.AsyncIOConnection:
        if not self.pool:
            self.pool = await edgedb.create_async_pool(
                dsn=self.dsn,
                host=self.host,
                port=self.port,
                admin=bool(self.admin),
                user=self.user,
                password=self.password,
                database=self.database,
                timeout=self.timeout,
                min_size=self.pool_min_size,
                max_size=self.pool_max_size,
            )
        return await self.pool.acquire()
