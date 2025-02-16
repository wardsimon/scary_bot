__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from tilthenightends.player import PlayerInfo

if TYPE_CHECKING:
    from scary_bot.players import Player
from tilthenightends import Vector, Towards

class MovementLogic:
    def __init__(self, player: 'Player'):
        self.vector = Vector(1, 1)
        self.position = Vector(0, 0)
        self.player = player

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        self.update_position(players)

    def get_self(self, players):
        return players.get(self.player.hero, None)

    def update_position(self, players):
        player = self.get_self(players)
        self.position = Vector(player.x, player.y)


class LeaderLogic(MovementLogic):
    def __init__(self, player: 'Player'):
        super().__init__(player)
        self.next_turn = 5.0
        self.initial_tick = 10
        self.tick = self.initial_tick

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        super().run(t, dt, monsters, players, pickups)
        if t > self.next_turn:
            pot = Potential(toward_poles(t, players, pickups), monster_poles(monsters))
            v = pot.direction(Vec(self.position.x, self.position.y))
            if v == Vector(0, 0):
                self.next_turn += 3
            else:
                self.vector  = v
                self.next_turn += 0.5
        return self.vector


class FollowerLogic(MovementLogic):
    def __init__(self, player: 'Player', leader: str):
        super().__init__(player)
        self.leader = leader
        self._first_leader = leader

    def get_leader(self, players):
        for name, player in players.items():
            if name == self.leader:
                return player
        return None

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        super().run(t, dt, monsters, players, pickups)
        leader = self.get_leader(players)
        if leader:
            angle = (t % 360) * (3.14159 / 180)  # Convert time to radians
            radius = 5  # Set the radius of the circle
            x_offset = radius * np.cos(angle)
            y_offset = radius * np.sin(angle)
            return Towards(leader.x + x_offset, leader.y + y_offset)
        # The leader is dead. I'm the new leader.
        self.player.is_leader = True
        self.player.follower.leader = None
        self.player.brain.leader.is_leader = False
        self.player.brain.followers[self.player.brain.leader.hero] = self.player.brain.leader
        self.player.brain.followers.pop(self.player.hero)
        for value in self.player.brain.followers:
            value.follower.leader = self.player.hero
        self.player.brain.leader = self.player
        return self.run(t, dt, monsters, players, pickups)
from tilthenightends import Levelup, LevelupOptions, Vector, Team, Towards
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
        total = goal - avoid
        norm = total.length()
        if norm:
            total *= 1/norm
        return Vector(total.x, total.y)


def monster_pole(info: MonsterInfo):
    # Avoid strong-fast monsters:
    strength = info.attacks * info.speeds
    return tuple(Pole(Vec(x, y), s, r) for x, y, s, r in zip(info.x, info.y, strength, info.radii))


def monster_poles(monsters):
    tot = []
    for named, values in monsters.items():
        tot += list(monster_pole(values))
    return tuple(tot)

def obj_poles(groups: dict, known: dict):
    tot = []
    for t, (s, r) in known.items():
        if t in groups:
            tot.extend([Pole(Vec(x, y), s, r) for x, y in zip(groups[t].x, groups[t].y)])
    return tuple(tot)

def healer_poles(t, players):
    if 'isolde' not in players:
        return ()
    water = players['isolde'].weapon.projectiles
    pos = water['positions']  # Always N by 2?
    if not len(pos):
        # No water to go towards
        return ()
    xs, ys = pos[:, 0], pos[:, 1]
    ss = (water['tends'] - t) * water['healths']
    rs = water['radii']
    return tuple(Pole(Vec(x, y), s, r) for x, y, s, r in zip(xs, ys, ss, rs))


def health_need(players: dict[str, PlayerInfo]):
    for name, player in players.items():
        if player.health and player.health < player.max_health:
            return 1
    return 0


def toward_poles(t, players, pickups):
    health_scale = health_need(players)
    known = {'chicken': (10 * health_scale, 100), 'treasure': (130, 100)}
    pickup_poles = obj_poles(pickups, known)
    player_poles = healer_poles(t, players) if health_scale else ()
    return player_poles + pickup_poles