"""
Data models.
"""
import dataclasses

from . import database

KNOWN_POSITIONS = {
    "pitcher",
    "catcher",
    "firstBase",
    "secondBase",
    "thirdBase",
    "shortstop",
    "leftField",
    "centerField",
    "rightField",
}


@dataclasses.dataclass
class Profile:
    """
    Models a player's personal profile.
    """

    name: str
    country: str
    year: int

    @classmethod
    def from_parts(cls, first_name, last_name, country, year):
        name = " ".join([first_name, last_name])
        return cls(name, country, year)


@dataclasses.dataclass
class Stats:
    """
    Models a player's performance statistics.
    """

    at_bats: int
    home_runs: int
    hits: int
    strikeouts: int
    batting_average: float
    slugging_percentage: float

    @classmethod
    def from_parts(cls, at_bats, hits, doubles, triples, home_runs, strikeouts):
        batting_average = hits / at_bats
        singles = hits - doubles - triples - home_runs
        slugging = (singles + (2 * doubles) + (3 * triples) + (4 * home_runs)) / at_bats

        return cls(
            at_bats, hits, home_runs, strikeouts, batting_average, slugging
        )

    @classmethod
    def average(cls, all_stats):
        count = len(all_stats)
        parts = {}
        for attr in {"at_bats", "home_runs", "hits", "strikeouts"}:
            if count == 0:
                parts[attr] = 0
            else:
                parts[attr] = int(sum(getattr(s, attr) for s in all_stats) / count)

        for attr in {"batting_average", "slugging_percentage"}:
            if count == 0:
                parts[attr] = 0
            else:
                parts[attr] = sum(getattr(s, attr) for s in all_stats) / count

        return cls(**parts)

@dataclasses.dataclass
class Lineup:
    """
    Models a lineup or team of players.
    """

    ident: int
    pitcher: str
    catcher: str
    firstBase: str
    secondBase: str
    thirdBase: str
    shortstop: str
    leftField: str
    centerField: str
    rightField: str


def get_db(path):
    """
    Helper to load a database at the given path.

    Arguments:
        path: Location of the database.

    Returns:
        An instance of database.Database.
    """
    db = database.Database(path)

    query = """
    CREATE TABLE IF NOT EXISTS "People" (
    	"playerID" TEXT UNIQUE,
    	"nameFirst" TEXT,
    	"nameLast" TEXT,
    	"birthYear" INTEGER,
    	"birthCountry" TEXT
    );
    """
    db.execute(query)

    query = """
    CREATE TABLE IF NOT EXISTS "Batting" (
    	"playerID" TEXT,
        "AB" INTEGER,
        "_2B" INTEGER,
        "_3B" INTEGER,
        "HR" INTEGER,
        "H" INTEGER,
        "SO" INTEGER
    );
    """
    db.execute(query)

    query = """
    CREATE TABLE IF NOT EXISTS "Lineups" (
    	"lineupId" INTEGER PRIMARY KEY AUTOINCREMENT
    );
    """
    db.execute(query)

    query = """
    CREATE TABLE IF NOT EXISTS "LineupAssignments" (
    	"lineupId" INTEGER,
        "position" TEXT,
        "playerId" TEXT,
        UNIQUE("lineupId", "position"),
        UNIQUE("lineupId", "playerId")
    );
    """
    db.execute(query)

    return db


def get_players(db, first_name, last_name):
    """
    Query for players whose first and last name start with the given prefixes,
    respectively.

    Arguments:
        db:         An instance of databases.Database.
        first_name: A string prefix for the first name.
        last_name:  A string prefix for the last name.

    Returns:
        A list of string player identifiers.
    """
    query = """
        SELECT
        playerId
        FROM People
        WHERE namefirst LIKE ? and namelast LIKE ?
        ORDER BY namefirst,namelast
   """
    output = []
    for result in db.fetchall(query, [f"{first_name}%", f"{last_name}%"]):
        (ident,) = result
        output.append(ident)

    return output


def get_profiles(db, idents):
    """
    Fetch player profiles.

    Arguments:
        db:     An instance of databases.Database.
        idents: A list of string player identifiers.

    Returns:
        A list of Profile objects.
    """
    placeholders = ",".join(["?"] * len(idents))
    query = (
        "SELECT"
        " playerId,namefirst,namelast,birthCountry,birthYear"
        " FROM People"
        f" WHERE playerId IN ({placeholders})"
    )
    mapping = {}
    for result in db.fetchall(query, idents):
        ident, first_name, last_name, country, year = result
        mapping[ident] = Profile.from_parts(first_name, last_name, country, year)

    output = []
    for ident in idents:
        try:
            output.append(mapping[ident])
        except KeyError:
            output.append(Profile("UNKNOWN", "UNK", 0))

    return output


def get_stats(db, idents):
    """
    Fetch player performance statistics.

    Arguments:
        db:     An instance of databases.Database.
        idents: A list of string player identifiers.

    Returns:
        A list of Stats objects.
    """
    placeholders = ",".join(["?"] * len(idents))
    query = (
        "SELECT"
        " playerId, SUM(AB), SUM(_2B), SUM(_3B), SUM(HR), SUM(H), SUM(SO)"
        " FROM Batting"
        f" WHERE playerId IN ({placeholders})"
        " GROUP BY playerId"
    )

    mapping = {}
    for result in db.fetchall(query, idents):
        ident, ab, dbl, tpl, hr, h, so = result
        mapping[ident] = Stats.from_parts(ab, h, dbl, tpl, hr, so)

    output = []
    for ident in idents:
        try:
            output.append(mapping[ident])
        except KeyError:
            output.append(Stats(*([0] * 6)))

    return output


def get_lineup(db, ident):
    """
    Fetch players in a lineup.

    Arguments:
        db:     An instance of databases.Database.
        ident:  An integer lineup identifier.

    Returns:
        A Lineup object.
    """
    query = """
        SELECT position,playerId
        FROM Lineups
        INNER JOIN LineupAssignments
        ON Lineups.lineupId = LineupAssignments.lineupId
        WHERE Lineups.lineupId=?
    """
    positions = dict((position, None) for position in KNOWN_POSITIONS)
    assignments = dict(db.fetchall(query, [ident]))
    return Lineup(ident, **(positions | assignments))


def create_lineup(db):
    """
    Creates a new lineup.

    Arguments:
        db:     An instance of databases.Database.

    Returns:
        A Lineup object.
    """
    query = "INSERT INTO Lineups VALUES(null)"
    ident = db.insertone(query)
    return get_lineup(db, ident)


def update_lineup(db, ident, **kwargs):
    """
    Updates a lineup.

    Arguments:
        db:     An instance of databases.Database.
        ident:  An integer lineup identifier.
        kwargs: (optional) A dictionary of position keys and string player identifier
                values, ex. {"pitcher": "foo"}. Pass None to unassign a given position.
                If no key is defined for a given position it will be left unchanged.

    Returns:
        An updated Lineup object.
    """
    data = []
    for position, query in kwargs.items():
        if position not in KNOWN_POSITIONS:
            continue

        # Allow ident or name combo
        player_id = query
        try:
            first_name, last_name = query.split(" ", maxsplit=1)
        except ValueError:
            first_name = query
            last_name = ""

        data.append([ident, position, player_id, f"{first_name}%", f"{last_name}%"])

    query = """
        INSERT OR REPLACE INTO LineupAssignments
        VALUES(
            ?,
            ?,
            (
                SELECT playerId
                FROM People
                WHERE playerId=?
                    OR (
                        namefirst LIKE ?
                        AND namelast LIKE ?
                    )
                LIMIT 1
            )
        )
    """

    db.insert(query, data)

    return get_lineup(db, ident)
