"""
A GraphQL server build using Ariadne.
"""
import pathlib

import aiodataloader
import ariadne
import ariadne.asgi

from . import models

try:
    db = models.get_db(pathlib.Path(__file__).parent.parent / "database.sqlite")
except FileNotFoundError as exc:
    raise ValueError("The database must be downloaded first, see README.md") from exc

type_defs = ariadne.gql(
    """
    type Query {
        player(playerId: String!): Player
        players(firstName: String!, lastName: String!): [Player]!
        lineup(lineupId: Int!): Lineup
    }

    type Player {
        playerId: String!
        profile: Profile!
        stats: Stats!
    }

    type Profile {
        name: String!
        country: String!
        year: Int!
    }

    type Stats {
        atBats: Int!
        homeRuns: Int!
        hits: Int!
        strikeouts: Int!
        battingAverage: Float!
        sluggingPercentage: Float!
    }

    type Mutation {
        lineup(
            lineupId: Int,
            pitcher: String,
            catcher: String,
            firstBase: String,
            secondBase: String,
            thirdBase: String,
            shortstop: String,
            leftField: String,
            centerField: String,
            rightField: String
        ): Lineup
    }

    type Lineup {
        lineupId: Int
        average: Stats
        pitcher: Player
        catcher: Player
        firstBase: Player
        secondBase: Player
        thirdBase: Player
        shortstop: Player
        leftField: Player
        centerField: Player
        rightField: Player
    }
"""
)


def encode_profile(profile):
    """
    Returns a dict representing the given profile.

    Arguments:
        profile: An instance of models.Profile
    """
    if profile is None:
        return None

    return {"name": profile.name, "country": profile.country, "year": profile.year}


def encode_lineup(lineup):
    """
    Returns a dict representing the given lineup.

    Arguments:
        profile: An instance of models.Lineup
    """
    if lineup is None:
        return None

    # Create like { "pitcher": { "playerId": "foo" }, ... }
    players = {}
    for key in models.KNOWN_POSITIONS:
        playerId = getattr(lineup, key)
        if playerId is None:
            continue

        players[key] = {"playerId": playerId}

    return {"lineupId": lineup.ident} | players


def encode_stats(stats):
    """
    Returns a dict representing the given player stats.

    Arguments:
        profile: An instance of models.Stats
    """
    if stats is None:
        return None

    return {
        "atBats": stats.at_bats,
        "homeRuns": stats.home_runs,
        "hits": stats.hits,
        "strikeouts": stats.strikeouts,
        "battingAverage": round(stats.batting_average, 3),
        "sluggingPercentage": round(stats.slugging_percentage, 3),
    }


query = ariadne.QueryType()


@query.field("player")
def resolve_player(obj, info, playerId):
    """
    Resolver for a player.

    Arguments:
        obj:        Not used.
        info:       Not used.
        playerId:   A string player identifier.
    """
    return {"playerId": playerId}


@query.field("players")
def resolve_players(obj, info, firstName, lastName):
    """
    Resolver for a list of players.

    Matches players whose first and last names start with the given prefixes.

    Arguments:
        obj:        Not used.
        info:       Not used.
        firstName:  A string prefix to match first names against.
        lastName:   A string prefix to mach last names against.
    """
    idents = models.get_players(db, firstName, lastName)
    return [{"playerId": ident} for ident in idents]


@query.field("lineup")
def resolve_lineup(obj, info, lineupId):
    """
    Resolver for a lineup or team of players.

    Arguments:
        obj:        Not used.
        info:       Not used.
        lineupId:   An integer lineup identifier created by this server.
    """
    lineup = models.get_lineup(db, lineupId)
    return encode_lineup(lineup)


player = ariadne.ObjectType("Player")


@player.field("profile")
async def resolve_player_profile(player, info):
    """
    Resolver for a details about a specific player.

    Arguments:
        player:     A dictionary whose key "playerId" maps to a player identifier.
        info:       Not used.
    """
    playerId = player["playerId"]
    loader = info.context["player_profile_loader"]
    profile = await loader.load(playerId)
    return encode_profile(profile)


@player.field("stats")
async def resolve_player_stats(player, info):
    """
    Resolver for all time stats for a specific player.

    Arguments:
        player:     A dictionary whose key "playerId" maps to a player identifier.
        info:       Not used.
    """
    playerId = player["playerId"]
    loader = info.context["player_stats_loader"]
    stats = await loader.load(playerId)
    return encode_stats(stats)


lineup = ariadne.ObjectType("Lineup")


@lineup.field("average")
async def resolve_lineup_average(lineup, info):
    """
    Resolver for summary stats for a lineup.
    """
    loader = info.context["player_stats_loader"]

    all_stats = []
    for key in models.KNOWN_POSITIONS:
        try:
            player = lineup[key]
            if player is not None:
                playerId = player["playerId"]
                stats = await loader.load(playerId)
                all_stats.append(stats)
        except KeyError:
            pass

    return encode_stats(models.Stats.average(all_stats))

mutation = ariadne.MutationType()


@mutation.field("lineup")
def resolve_mutate_lineup(obj, info, lineupId=None, **kwargs):
    """
    Mutator for a lineup.

    Arguments:
        lineupId:   (optional) A lineup identifier. If None, a new lineup will be
                    created.
        **kwargs:   (optional) Keys must be position names (ie. "pitcher" or "leftField")
                    and values must be string player identifiers.
    """
    if lineupId is None:
        # Create new lineup
        lineup = models.create_lineup(db)
        lineupId = lineup.ident

    lineup = models.update_lineup(db, lineupId, **kwargs)
    return encode_lineup(lineup)


async def get_stats_from_db(idents):
    """
    Helper to fetch a collection of player stats.

    Arguments:
        idents: A list of string player identifiers.
    """
    stats = models.get_stats(db, idents)
    return stats


async def get_profiles_from_db(idents):
    """
    Helper to fetch a collection of player profiles.

    Arguments:
        idents: A list of string player identifiers.
    """
    profiles = models.get_profiles(db, idents)
    return profiles


def get_context_value(request):
    """
    Context value getter.
    """
    return {
        "request": request,
        "player_stats_loader": aiodataloader.DataLoader(get_stats_from_db),
        "player_profile_loader": aiodataloader.DataLoader(get_profiles_from_db),
    }


schema = ariadne.make_executable_schema(type_defs, [query, player, lineup, mutation])

app = ariadne.asgi.GraphQL(schema, context_value=get_context_value, debug=True)
