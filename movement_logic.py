__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from scary_bot.players import BasePlayer
from tilthenightends import Vector, Towards

class MovementLogic:
    def __init__(self, player: 'BasePlayer'):
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
    def __init__(self, player: 'BasePlayer'):
        super().__init__(player)
        self.next_turn = 5.0
        self.initial_tick = 10
        self.tick = self.initial_tick

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        super().run(t, dt, monsters, players, pickups)
        if t > self.next_turn:
            pot = Potential(pickup_poles(pickups), monster_poles(monsters))
            v = pot.direction(Vec(self.position.x, self.position.y))
            if v == Vector(0, 0):
                self.next_turn += 3
            else:
                self.vector  = v
                self.next_turn += 0.5
        return self.vector


class FollowerLogic(MovementLogic):
    def __init__(self, player: 'BasePlayer', leader: str):
        super().__init__(player)
        self.leader = leader

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
        return Vector(total.x, total.y)


def obj_poles(groups: dict, known: dict):
    tot = []
    for t, (s, r) in known.items():
        if t in groups:
            tot.extend([Pole(Vec(x, y), s, r) for x, y in zip(groups[t].x, groups[t].y)])
    return tuple(tot)


def monster_poles(monsters):
    known = {'bat': (1, 50)}
    return obj_poles(monsters, known)


def pickup_poles(pickups):
    known = {'chicken': (10, 100), 'box': (100, 130)}
    return obj_poles(pickups, known)
