# How to Connect to EdgeDB in Python
EdgeDB is 'an Object-Relation Database'. That's a funcy way of saying that it's a hybrid between tabular systems (like Postgres and MySQL) and document- style or graph-like systems(like MongoDB or Neo4j). Its feature set is really impressive but for this article we're going to focus on one small task: connecting to the database from Python. No queries, no schema; just one thing in (hopefully) a digestable amount of detail. We're going to use a few recent Python features as well: type annotations, dataclasses, f-strings and enums.

**Our Goals**:
 - Connect Synchronously
 - Test this so we can prove we're not crazy
 - Connect Asynchronously
 - Connect with an Asynchronus Pool
 - Switch back and forth between async and sync as appropriate

## Setting up
For this tutorial you're going to want have Docker and Python 3.8 installed. If you're not fluent  with Docker, don't worry. We're going to be running one command and then ignoring it while it runs EdgeDB in the background.

You'll want to have _some_ kind of virtual environment. For this experiment we'll be using Poetry, but venv, Pipenv or Dephell would work just as well.

```bash
@agritheory:~$ mkdir edgedb_connect
@agritheory:~$ cd edgedb_connect
@agritheory:~/edgedb_connect$ poetry init
This command will guide you through creating your pyproject.toml config.

Package name [edgedb_connect]:  
Version [0.1.0]:  
Description []:  
Author [Tyler Matteson <tyler@agritheory.com>, n to skip]:  
License []:  
Compatible Python versions [^3.8]:  

Would you like to define your main dependencies interactively? (yes/no) [yes] yes
You can specify a package in the following forms:
  - A single name (requests)
  - A name and a constraint (requests ^2.23.0)
  - A git url (git+https://github.com/python-poetry/poetry.git)
  - A git url with a revision (git+https://github.com/python-poetry/poetry.git#develop)
  - A file path (../my-package/my-package.whl)
  - A directory (../my-package/)
  - An url (https://example.com/packages/my-package-0.1.0.tar.gz)

Search for package to add (or leave blank to continue): edgedb
Found 3 packages matching edgedb

Enter package # to add, or the complete package name if it is not listed:
 [0] edgedb
 [1] edgeql-queries
 [2] edb
 > 0
Enter the version constraint to require (or leave blank to use the latest version):
Using version ^0.7.1 for edgedb

Add a package:

Would you like to define your development dependencies interactively? (yes/no) [yes] no
Generated file

[tool.poetry]
name = "edgedb_connect"
version = "0.1.0"
description = ""
authors = ["Tyler Matteson <tyler@agritheory.com>"]

[tool.poetry.dependencies]
python = "^3.8"
edgedb = "^0.7.1"

[tool.poetry.dev-dependencies]

[build-system]
requires = ["poetry>=0.12"]
build-backend = "poetry.masonry.api"


Do you confirm generation? (yes/no) [yes] yes
```

Cool. Now let's get that Docker thing going. We'll only be using the 5656 port and won't be binding any data, so don't take this as instructions for running an EdgeDB docker container _correctly_. In a **new terminal window**:

```bash
@agritheory:~/edgedb_connect$ docker run -it --rm -p 5656:5656 -p 8888:8888 -p 8889:8889 edgedb/edgedb
```


## Let's make a Connection Object

Now let's create a file and write some Python.
```bash
@agritheory:~/edgedb_connect$ touch connect.py
```
In our new `connect.py` file, let's import all of our dependencies:
```python
from __future__ import annotations

import typing
from enum import Enum
from dataclasses import dataclass

import edgedb
```

OK. Without going into too much detail we're going to use a Dataclass to store our connection parameters. The attribute names will match the API for connection parameters as documented in the EdgeDB Python client.
```python
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
```
It turns out there quite a few options available for connecting to EdgeDB. We're _not_ going to be using the DSN API and we _will_ be defaulting to connecting over a UNIX socket on the default port of 5656, which you may remember seeing in the Docker command. (The 8888 and 8889 ports are used for HTTP and GraphQL and those features are out of scope for this article.)

OK. Let's write a class method to connect to EdgeDB.
```python
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
```
Between these type hints and the ones from the class declaration it should be pretty easy to see what's going on here. We're creating a wrapper acound the connection parameters and a way to call it: `edgedb.connect()`

## This is not TDD. It's 'testing early'.


That all looks like it should work and if you wanted to, you could import it into the repl and start interacting with EdgeDB. But we're not goign to do that. We're going to be good citizens and write a test that tests this method.

To get started with the testing, we'll need to add some dependencies to our project. (We're going to add pytest's asyncio utils here premtively).
```bash
@agritheory:~/edgedb_connect$ poetry add pytest pytest-asyncio --dev
Using version ^5.4.1 for pytest
Using version ^0.10.0 for pytest-asyncio

Updating dependencies
Resolving dependencies... (0.6s)

Writing lock file

Package operations: 11 installs, 0 updates, 0 removals

  - Installing pyparsing (2.4.7)
  - Installing six (1.14.0)
  - Installing attrs (19.3.0)
  - Installing more-itertools (8.2.0)
  - Installing packaging (20.3)
  - Installing pluggy (0.13.1)
  - Installing py (1.8.1)
  - Installing wcwidth (0.1.9)
  - Installing pytest (5.4.1)
  - Installing edgedb (0.7.1)
  - Installing pytest-asyncio (0.10.0)
@agritheory:~/edgedb_connect$ touch test.py
```
OK, in our newly created `test.py` file let's see what we can break. First our dependencies:
```python
import typing
import pytest
import edgedb
from connect import EdgeDBConnection
```
The Docker image uses `'edgedb'` for user, password and database name. Since we want reuse these connection parameters for all of our tests, we're going to create a pytest fixture. Pytest fixtures allow you to share a variable or object between multiple tests by passing it into the test function as an argument.

```python
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
```
The hardest part of writing tests is getting started. The next hardest part is deciding what to test. In this case lets start with a simple sanity check on our fixture. If this test passes then we've confimed that our fixture is behaving as expected.

```python
@pytest.mark.usefixtures("connection_object")
def test_connection_object(connection_object) -> None:
    assert connection_object.host == "localhost"
    assert connection_object.port == 5656
    assert connection_object.admin is False
    assert connection_object.timeout == 60
    assert connection_object.user == "edgedb"
    assert connection_object.password == "edgedb"
    assert connection_object.database == "edgedb"
```
Let's run this test:
```
@agritheory:~/edgedb_connect$ poetry shell
(.venv) @agritheory:~/edgedb_connect$ python -m pytest test.py
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 1 item                                                                                                                                     

test.py .                                                                                                                                      [100%]

================================================================= 1 passed in 0.03s ==================================================================
```
Well that's a relief. But we haven't actually connect to EdgeDB yet. Let's write a test for that.
```python
@pytest.mark.usefixtures("connection_object")
def test_edgedb_sync_connection(connection_object) -> None:
    sync_connection = connection_object.connect_sync()
    assert isinstance(sync_connection, edgedb.BlockingIOConnection)
    sync_connection.close()
    assert sync_connection.is_closed() is True
```
Since it's polite to close your database connection when you're done with it, we'll do that and assert that it is actually close. Both the `close` and `is_closed` methods are coming from the `BlockingIOConnection` class. Let's run the test.
```
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 2 items                                                                                                                                    

test.py ..                                                                                                                                     [100%]

================================================================= 2 passed in 0.79s ==================================================================
```
Cool. If you never want to use the Async functionality of the EdgeDB library, go ahead and bail now, but we haven't gotten to the best part yet.

## Time Warp
Let's add some async functionality to this class so we can reuse the same connection parameter boilerplate.

```python
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
```
That's barely different than the synchronus connection method! That can't be right. Let's write a test to find out.
```python
@pytest.mark.usefixtures("connection_object")
@pytest.mark.asyncio
async def test_edgedb_async_connections(connection_object) -> typing.NoReturn:
    async_connection = await connection_object.connect_async()
    assert isinstance(async_connection, edgedb.AsyncIOConnection)
    await async_connection.aclose()
    assert async_connection.is_closed() is True
```
Test results:
```
(.venv) @agritheory:~/edgedb_connect$ python -m pytest test.py
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 3 items                                                                                                                                    

test.py ...                                                                                                                                    [100%]

================================================================== warnings summary ==================================================================
.venv/lib/python3.8/site-packages/pytest_asyncio/plugin.py:39
  /home/tyler/edgedb_connect/.venv/lib/python3.8/site-packages/pytest_asyncio/plugin.py:39: PytestDeprecationWarning: direct construction of Function has been deprecated, please use Function.from_parent
    item = pytest.Function(name, parent=collector)

.venv/lib/python3.8/site-packages/pytest_asyncio/plugin.py:45
  /home/tyler/edgedb_connect/.venv/lib/python3.8/site-packages/pytest_asyncio/plugin.py:45: PytestDeprecationWarning: direct construction of Function has been deprecated, please use Function.from_parent
    item = pytest.Function(name, parent=collector)  # To reload keywords.

-- Docs: https://docs.pytest.org/en/latest/warnings.html
=========================================================== 3 passed, 2 warnings in 1.71s ============================================================
```
That's _also_ barely different. True, but the use of the `pytest-asyncio` provided decorator is required. If you don't install it, pytest will let you know that you should have and skip the test. You may see some warning from pytest about 'direct construction of Function has been deprecated'... it's not your fault, `pytest-asyncio` needs to accomodate differences in Python's asycio API from 3.5 to 3.8. You can safely ignore this warning.

## Let's make a pool
The pooled interface is really cool. It allows you to create and allocate async connections to a database without having to re-establish each time.
Let's implement that:
```python
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
```
This function need a couple more parameters, so we'll have to add those to the dataclass as well:
```python
timeout: int = 60
pool: typing.Optional[edgedb.AsyncIOPool] = None
pool_min_size: int = 1
pool_max_size: int = 1
```
And let's test that that interface works.
```python
@pytest.mark.usefixtures("connection_object")
@pytest.mark.asyncio
async def test_edgedb_async_pool(connection_object) -> None:
    async_pool = await connection_object("POOL")
    assert isinstance(async_pool, edgedb.AsyncIOConnection)
    await async_pool.aclose()
```
Let's also silence those warnings from pytest.
```
(.venv) @agritheory:~/edgedb_connect$ python -m pytest test.py -p no:warnings
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 4 items                                                                                                                                    

test.py ....                                                                                                                                   [100%]

================================================================= 4 passed in 2.45s ==================================================================
```

## An Await Agnostic Interface
Great! We can now connect in several different ways from the same object. But this could still be improved. What if we wanted to store the same connection type (sync/async/pool) and connect that way each time by default?
Well, we know our connection options, so let's put those in an enum and add a preference to our dataclass:
```python
class ConnectionType(Enum):
    SYNC = 1
    ASYNC = 2
    POOL = 3

# and in the dataclass
  pool_max_size: int = 1
  connection_type: ConnectionType = 'ASYNC'
```
So how are we going to do this? We can use the EdgeDBConnection object's `__call__` method and return the preferred connection type from there.
```python
def __call__(
        self, connection_type: ConnectionType = "SYNC"
    ) -> typing.Union[
        edgedb.BlockingIOConnection,
        typing.Coroutine[typing.Any, typing.Any, edgedb.AsyncIOConnection],
    ]:
        if connection_type not in ('SYNC', 'ASYNC', 'POOL'):
            raise TypeError(
                f"'connection_type' must be one of 'SYNC', 'ASYNC' or 'POOL'. \
                You provided '{connection_type}'"
            )
        self.connection_type = connection_type
        if self.connection_type == "ASYNC":
            return self.connect_async()
        if self.connection_type == "SYNC":
            return self.connect_sync()
        if self.connection_type == "POOL":
            return self.connect_async_pool()
```
Included is a validation for `connection_type` which enforces we don't do something like pass in 'sync' instead of 'SYNC'. Ask me how I know.
```python
@pytest.mark.usefixtures("connection_object")
@pytest.mark.xfail
def test_edgedb_enum_validator(connection_object) -> typing.NoReturn:
    sync_connection = connection_object("sync")
```
```
(.venv) @agritheory:~/edgedb_connect$ python -m pytest test.py -p no:warnings
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 5 items                                                                                                                                    

test.py ....x                                                                                                                                  [100%]

============================================================ 4 passed, 1 xfailed in 2.48s ============================================================
```
So let's use this failing example to refactor our other tests.
```python
# in test_edgedb_sync_connection
sync_connection = connection_object("SYNC")
# in test_edgedb_async_connections
async_connection = await connection_object("ASYNC")
# in test_edgedb_async_pool
async_pool = await connection_object("POOL")
```
And test:
```
================================================================ test session starts =================================================================
platform linux -- Python 3.8.2, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/tyler/edgedb_connect
plugins: asyncio-0.10.0
collected 5 items                                                                                                                                    

test.py ....x                                                                                                                                  [100%]

============================================================ 4 passed, 1 xfailed in 2.39s ============================================================
```
## But why is that useful?
Fair question. If you were to integrate the `edgedb` library into an application like Quart or Starlette, you might want to establish a connection and load some of the application's state in an intentionally blocking way and then switch to a non-blocking pattern later on. You could set the default to `'ASYNC'` or `'POOL'` but do that intial loading by passing `'SYNC'` to the connection instance. Things that are running in an event loop still need `await` in front of them.

## This isn't the end
Honestly, this is one of the least interesting aspects of EdgeDB. But maybe this is interesting enough for you to go out and look at [EdgeDB's features](https://edgedb.com/roadmap/), like it's killer schema, built in validations or that it will natively serve you GraphQL.

If you'd like to look at this code in it's finished form, [it's here](https://github.com/agritheory/edgedb_connections).
