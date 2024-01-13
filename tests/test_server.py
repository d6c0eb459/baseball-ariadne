"""
Tests for the server module.
"""
import pathlib
import unittest

from src import models
from src import server

from . import utils


class MockInfo:
    """
    Mocks ariadne's Info object.
    """
    @property
    def context(self):
        return server.get_context_value(None)


class TestServer(unittest.IsolatedAsyncioTestCase):
    """
    Tests for server.
    """

    async def asyncSetUp(self):
        self._db = models.get_db(":memory:")
        utils.init_db(self._db)

        self._server_db = server.db
        server.db = self._db

    async def asyncTearDown(self):
        server.db = self._server_db
        self._db.close()

    def test_resolve_player(self):
        actual = server.resolve_player(None, None, "foo")
        expected = {"playerId": "foo"}
        self.assertEqual(actual, expected)

    def test_resolve_players(self):
        actual = server.resolve_players(None, None, "B", "B")
        expected = [{"playerId": "3"}, {"playerId": "2"}]
        self.assertEqual(actual, expected)

    async def test_resolve_stats(self):
        actual = await server.resolve_player_stats({"playerId": "1"}, MockInfo())
        expected = {
            "atBats": 100,
            "homeRuns": 10,
            "hits": 10,
            "strikeouts": 10,
            "battingAverage": 10 / 100,
            "sluggingPercentage": 91 / 100,
        }
        self.assertEqual(actual, expected)

    async def test_resolve_profile(self):
        actual = await server.resolve_player_profile({"playerId": "1"}, MockInfo())
        expected = {"name": "Andy Anderson", "country": "CAN", "year": 2000}
        self.assertEqual(actual, expected)
