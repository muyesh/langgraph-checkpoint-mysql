import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
import pymysql.constants.ER
from pymysql.cursors import DictCursor
from typing_extensions import Self, override

from langgraph.checkpoint.mysql import BaseSyncMySQLSaver, _get_connection
from langgraph.checkpoint.mysql import Conn as BaseConn

Conn = BaseConn[pymysql.Connection]


class PyMySQLSaver(BaseSyncMySQLSaver[pymysql.Connection, DictCursor]):
    @classmethod
    @contextmanager
    def from_conn_string(
        cls,
        conn_string: str,
    ) -> Iterator[Self]:
        """Create a new PyMySQLSaver instance from a connection string.

        Args:
            conn_string (str): The MySQL connection info string.

        Returns:
            PyMySQLSaver: A new PyMySQLSaver instance.

        Example:
            conn_string=mysql+aiomysql://user:password@localhost/db?unix_socket=/path/to/socket
        """
        parsed = urllib.parse.urlparse(conn_string)

        # In order to provide additional params via the connection string,
        # we convert the parsed.query to a dict so we can access the values.
        # This is necessary when using a unix socket, for example.
        params_as_dict = dict(urllib.parse.parse_qsl(parsed.query))

        with pymysql.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password or "",
            database=parsed.path[1:],
            port=parsed.port or 3306,
            unix_socket=params_as_dict.get("unix_socket"),
            autocommit=True,
        ) as conn:
            yield cls(conn)

    @override
    @staticmethod
    def _is_no_such_table_error(e: Exception) -> bool:
        return (
            isinstance(e, pymysql.ProgrammingError)
            and e.args[0] == pymysql.constants.ER.NO_SUCH_TABLE
        )

    @override
    @contextmanager
    def _cursor(self) -> Iterator[DictCursor]:
        with _get_connection(self.conn) as conn:
            with self.lock, conn.cursor(DictCursor) as cur:
                yield cur


__all__ = ["PyMySQLSaver", "Conn"]
