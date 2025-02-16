# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from dataclasses import dataclass
from scary_bot.players import Player
from tilthenightends import Levelup, LevelupOptions, Team
RNG = np.random.default_rng(seed=12)


heroes = {
    "isolde": ['player_health', 'weapon_cooldown', 'weapon_damage', 'weapon_size'],
    "evelyn": ['player_health', 'weapon_cooldown', 'weapon_speed', 'weapon_damage', 'weapon_size'],
    "theron": ['player_health', 'weapon_cooldown', 'weapon_damage', 'weapon_size'],
    "selene": ['player_health', 'weapon_cooldown', 'weapon_damage', 'weapon_size'],
    "seraphina": ['player_health', 'weapon_cooldown', 'weapon_damage', 'weapon_size'],
}
heroes_list = list(heroes.keys())
heroes_inverted = {
    "player_health": ["isolde", "evelyn", "theron", "selene", "seraphina"],
    "weapon_speed": ["evelyn"],
    "weapon_cooldown": ["isolde", "evelyn", "theron", "selene", "seraphina"],
    "weapon_damage": ["isolde", "theron", "selene", "seraphina"],
    "weapon_size": ["isolde", "evelyn", "theron", "selene", "seraphina"],
}
heroes_flat = [(hero, attr) for hero, attrs in heroes_inverted.items() for attr in attrs]

class Brain:
    def __init__(self):
        self.followers = {}
        self.leader = None
        self.levelup_index = 0

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
        what, hero = heroes_flat[self.levelup_index % len(heroes_flat)]
        self.levelup_index += 1
        return Levelup(hero, LevelupOptions[what])

brain = Brain()
players = [brain.create_hero(heroes_list[0], None, is_primary_hero=True) ] + [brain.create_hero(hero, heroes_list[0]) for hero in heroes_list[1:]]

team = Team(
    players=players,
    strategist=brain
)
