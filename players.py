__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

from abc import ABCMeta, abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scary_bot.bot import Brain
from scary_bot.movement_logic import LeaderLogic, FollowerLogic
from tilthenightends import Vector, Towards


class BasePlayer(metaclass=ABCMeta):
    def __init__(self, hero: str, is_leader = False):
        super().__init__()
        self.hero = hero
        self.leader = LeaderLogic(self)
        self.follower = FollowerLogic(self, None)
        self.is_leader = is_leader

    @abstractmethod
    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        pass


class Player(BasePlayer):
    def __init__(self, brain: 'Brain', hero: str, following: str):
        super().__init__(hero)
        self.brain = brain
        self.follower.leader = following

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        # If the player is a leader, run the leader logic

        if self.is_leader:
            return self.leader.run(t, dt, monsters, players, pickups)
        # Otherwise, follow the player
        else:
            return self.follower.run(t, dt, monsters, players, pickups)
