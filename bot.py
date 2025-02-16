# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from tilthenightends import Levelup, LevelupOptions, Vector, Team, Towards
from dataclasses import dataclass

from tilthenightends.monsters import MonsterInfo

RNG = np.random.default_rng(seed=12)


@dataclass
class Vec:
    x: float
    y: float

    def length(self):
        return np.sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, o):
        return Vec(self.x + o.x, self.y + o.y)

    def __radd__(self, o):
        if not isinstance(o, Vec):
            return Vec(o + self.x, o + self.y)  # needed for sum()
        return Vec(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Vec(self.x - o.x, self.y - o.y)

    def __mul__(self, scalar: float):
        return Vec(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float):
        return Vec(scalar * self.x, scalar * self.y)


@dataclass
class Pole:
    pos: Vec
    strength: float
    sigma: float
    scale: float = 1.0

    def __post_init__(self):
        self.scale = 1.0 / self.sigma / self.sigma

    def direction(self, pos: Vec):
        v = self.pos - pos
        r = v.length()
        magnitude = self.strength * np.exp(-r * r * self.scale)
        return (magnitude / r) * v


@dataclass
class Potential:
    attract: tuple[Pole, ...]  # TODO it would be great if this was a PriorityQueue
    repulse: tuple[Pole, ...]  # TODO PriorityQueue this up too

    def direction(self, pos: Vec) -> Vector:
        """Select a direction from (x,y) that avoids repulsive poles"""
        # To start, just go for the first-known attractor
        goal = self.attract[0].direction(pos) if len(self.attract) else Vec(0, 0)
        # but try to avoid all known repulsive poles
        avoid = sum(rep.direction(pos) for rep in self.repulse) if len(self.repulse) else Vec(0, 0)
        print(f'{len(self.attract)=} {goal=} {len(self.repulse)=} {avoid=}')
        total = goal - avoid
        norm = total.length()
        if norm:
            total *= 1/norm
        return Vector(total.x, total.y)


def monster_pole(info: MonsterInfo):
    strength = info.attacks * info.speeds
    return tuple(Pole(Vec(x, y), s, r) for x, y, s, r in zip(info.x, info.y, strength, info.radii))


def obj_poles(groups: dict, known: dict):
    tot = []
    for t, (s, r) in known.items():
        if t in groups:
            tot.extend([Pole(Vec(x, y), s, r) for x, y in zip(groups[t].x, groups[t].y)])
    return tuple(tot)


def monster_poles(monsters):
    tot = []
    for named, values in monsters.items():
        tot += list(monster_pole(values))
    return tuple(tot)

def pickup_poles(pickups):
    known = {'chicken': (10, 100), 'treasure': (100, 130)}
    return obj_poles(pickups, known)


class Leader:
    def __init__(self, hero: str):
        self.hero = hero
        self.next_turn = 0.5
        self.vector = Vector(1, 1)

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        if t > self.next_turn:
            pot = Potential(pickup_poles(pickups), monster_poles(monsters))
            v = pot.direction(Vec(players[self.hero].x, players[self.hero].y))
            if v == Vector(0, 0):
                self.next_turn += 3
            else:
                self.vector  = v
                self.next_turn += 0.5
        return self.vector


class Follower:
    def __init__(self, hero: str, following: str):
        self.hero = hero
        self.following = following

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        for name, player in players.items():
            if name == self.following:
                return Towards(player.x, player.y)
        return None


class Brain:
    def __init__(self):
        pass

    def levelup(self, t: float, info: dict, players: dict) -> Levelup:
        # A very random choice
        hero = RNG.choice(list(players.keys()))
        what = RNG.choice(list(LevelupOptions))
        return Levelup(hero, what)


team = Team(
    players=[
        Leader(hero="alaric"),
        Follower(hero="kaelen", following="alaric"),
        Follower(hero="garron", following="alaric"),
        Follower(hero="isolde", following="alaric"),
        Follower(hero="lyra", following="alaric"),
    ],
    strategist=Brain(),
)
