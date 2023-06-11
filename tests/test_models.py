"""
Tests for the models module.
"""
import pathlib
import unittest

from src import models

from . import utils


class TestModels(unittest.TestCase):
    """
    Tests for models.
    """

    def setUp(self):
        self._db = models.get_db(":memory:")
        utils.init_db(self._db)

    def tearDown(self):
        self._db.close()

    def test_average_stats(self):
        """
        Test averating multiple stats.
        """
        stats = [
            models.Stats(50, 7, 6, 8, 14 / 100, 106 / 100),
            models.Stats(100, 10, 10, 10, 10 / 100, 91 / 100),
        ]
        actual = models.Stats.average(stats)
        expected = models.Stats(at_bats=75, home_runs=8, hits=8, strikeouts=9.0,
                batting_average=(0.14 + 0.1) / 2, slugging_percentage=(1.06 + 0.91) / 2)
        self.assertEqual(actual, expected)


    def test_get_players(self):
        """
        Test searching for players.
        """
        actual = models.get_players(self._db, "B", "B")
        expected = ["3", "2"]
        self.assertEqual(actual, expected)

    def test_get_profiles(self):
        """
        Test fetching player profiles.
        """
        actual = models.get_profiles(self._db, ["1", "2"])
        expected = [
            models.Profile("Andy Anderson", "CAN", 2000),
            models.Profile("Bob Ball", "CAN", 2001),
        ]
        self.assertEqual(actual, expected)

    def test_get_stats(self):
        """
        Test fetching player stats.
        """
        actual = models.get_stats(self._db, ["2", "1"])
        expected = [
            models.Stats(50, 7, 6, 8, 14 / 100, 106 / 100),
            models.Stats(100, 10, 10, 10, 10 / 100, 91 / 100),
        ]
        self.assertEqual(actual, expected)

    def test_create_lineup(self):
        """
        Test creating a lineup.
        """
        actual = models.create_lineup(self._db)
        expected = models.Lineup(1, *([None] * 9))
        self.assertEqual(actual, expected)

        actual = models.create_lineup(self._db)
        expected = models.Lineup(2, *([None] * 9))
        self.assertEqual(actual, expected)

    def test_get_lineup(self):
        """
        Test fetching a lineup.
        """
        actual = models.create_lineup(self._db)
        expected = models.Lineup(1, *([None] * 9))
        self.assertEqual(actual, expected)

    def test_update_lineup(self):
        """
        Test updating a lineup.
        """
        lineup = models.create_lineup(self._db)
        actual = models.update_lineup(
            self._db,
            lineup.ident,
            pitcher="1",
            catcher="2",
            firstBase="bork",
            rightField="3",
        )
        expected = models.Lineup(
            lineup.ident, "1", "2", None, None, None, None, None, None, "3"
        )
        self.assertEqual(actual, expected)

    def test_update_lineup_by_name(self):
        """
        Test updating a lineup using a player's name.
        """
        lineup = models.create_lineup(self._db)
        actual = models.update_lineup(
            self._db,
            lineup.ident,
            pitcher="Andy Anderson",
            catcher="B B",
            firstBase="Charlie",
            secondBase="Bork bork",
        )
        expected = models.Lineup(
            lineup.ident, "1", "2", "4", None, None, None, None, None, None
        )
        self.assertEqual(actual, expected)

    def test_lineup_unique(self):
        """
        Test lineup uniqueness.
        """
        lineup = models.create_lineup(self._db)

        # Test same player twice
        actual = models.update_lineup(
            self._db,
            lineup.ident,
            pitcher="Andy Anderson",
            catcher="Andy Anderson",
        )
        expected = models.Lineup(
            lineup.ident, None, "1", None, None, None, None, None, None, None
        )
        self.assertEqual(actual, expected)

        # Test same position twice
        actual = models.update_lineup(
            self._db,
            lineup.ident,
            catcher="Bob Ball",
        )
        expected = models.Lineup(
            lineup.ident, None, "2", None, None, None, None, None, None, None
        )
        self.assertEqual(actual, expected)
