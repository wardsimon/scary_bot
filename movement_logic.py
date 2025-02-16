__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

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
        self.tick -=1
        if self.tick > 0:
            return Vector(self.position.x, self.position.y)
        self.tick = self.initial_tick
        if t > self.next_turn:
            if pickups:
                chickens = []
                treasure = []
                chicken_object = pickups.get('chicken', None)
                if chicken_object:
                    for x, y in zip(chicken_object.x, chicken_object.y):
                        chickens.append(Vector(x, y))
                treasure_object = pickups.get('treasure', None)
                if treasure_object:
                    for x, y in zip(treasure_object.x, treasure_object.y):
                        treasure.append(Vector(x, y))
                distance_fn = lambda item:  ((item.x - self.position.x)**2 + (item.y - self.position.y)**2)**0.5
                chickens.sort(key=distance_fn)
                treasure.sort(key=distance_fn)
                if len(treasure) > 0:
                    return Towards(treasure[0].x, treasure[0].y)
                if len(chickens) > 0:
                    return Towards(chickens[0].x, chickens[0].y)
            self.next_turn += 5.0
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
        leader = self.get_leader(players)
        if leader:
            angle = (t % 360) * (3.14159 / 180)  # Convert time to radians
            radius = 5  # Set the radius of the circle
            x_offset = radius * np.cos(angle)
            y_offset = radius * np.sin(angle)
            return Towards(leader.x + x_offset, leader.y + y_offset)