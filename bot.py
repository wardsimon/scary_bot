# SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass
import numpy as np
from scary_bot.players import Player
from tilthenightends import Levelup, LevelupOptions, Team

RNG = np.random.default_rng(seed=12)

class Brain:
    def __init__(self):
        self.followers = {}
        self.leader = None

    def create_hero(self, hero: str, following: str, is_primary_hero: bool = False) -> Player:
        player = Player(brain, hero, following)
        if is_primary_hero:
            player.is_leader = True
            self.leader = player
        else:
            self.followers[hero] = player
        return player

    def levelup(self, t: float, info: dict, players: dict) -> Levelup:
        # A very random choice
        hero = RNG.choice(list(players.keys()))
        what = RNG.choice(list(LevelupOptions))
        return Levelup(hero, what)

brain = Brain()
players = []
players.append(brain.create_hero("alaric", None, is_primary_hero=True))
players.append(brain.create_hero("kaelen", "alaric"))
players.append(brain.create_hero("garron", "alaric"))
players.append(brain.create_hero("isolde", "alaric"))
players.append(brain.create_hero("lyra", "alaric"))

team = Team(
    players=players,
    strategist=brain
)
