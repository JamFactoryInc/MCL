from __future__ import annotations
from typing import Generic, Tuple, Dict, List, Optional


print(
    f"""\033[93mRemember that compiling with MCL will never be as fast as writing a datapack yourself.
Many things require workarounds to function as expected: strings, dicts, lists, and even basic arithmetic.
To make the final code significantly faster, use class functions wherever you can.
For example, a + b is a general operation, and at runtime, the types must be checked in order to retain all the data.
Instead, int.add(a, b) or double.add(a, b) can be used to skip this type check

Other examples include .get() for dictionaries\033[0m""")

class random:
    def randint(a,b):
        """Fetch a random integer between a and b inclusive
        """

class Scoreboard:
    class Objective:
        def __init__(self, name:str) -> None:
            pass
    class Variable:
        def __init__(self, value:int) -> None:
            pass
        def get_value(self):
            pass


class immutable_str:
    """
    The only vallid members are __eq__, __len__, __add__, __mul__, __ne__
    """
    def read(callback:function):
        """Once the immutable string has been read into a normal string,
        the callback function will be called with the resulting string passed into it.
        Reading can take multiple gameticks.

        Args:
            callback (function): function to call after string has been read
        """
        pass

def type(object:Any) -> immutable_str:
    """Returns an immutable string object representing the type of the passed-in object
    """
    pass

def print(text, color=None):
    pass

class Command:
    """
    Command is a container for implementations of vanilla minecraft commands

    Please note that commands can only be passed literals
    """
    def title(text):
        print(f'Displayed title {text}')

    def subtitle(text):
        print(f'Displayed title {text}')

    def fill(pos1, pos2):
        """[summary]

        Args:
            pos1 ([type]): [description]
            pos2 ([type]): [description]
        """
        pass

class Dimension:
    OVERWORLD = ''
    END = ''
    NETHER = ''

class Position:
    def __init__(self, x: int, y: int, z: int, dimension=Dimension.OVERWORLD):
        print('')

    @staticmethod
    def pos(self):
        return (self.x, self.y, self.z)

class Container:
    def __init__(self, capacity):
        pass
class Inventory(Container):
    def __init__(self):
        pass
    def get_armor_item(self):
        pass

class Entity:
    NEAREST_PLAYER = None
    ALL_PLAYERS = None
    RANDOM_ENTITY = None
    ALL_ENTITIES = None
    SELF = None
    class Generic:
        def __init__(self, position: Position):
            pass
        def find(self, type = None, x = None, y = None, z = None,
                 dimension = Dimension.OVERWORLD) -> Entity.Generic:
            pass
        @staticmethod
        def position(self):
            pass
    class Player(Generic):
        """
        Player cannot be instantiated and is partially readonly
        """
        def __init__(self, position) -> Entity.Player:
            self.inventory


def select(selector: str, type=Entity, limit=1):
    return Entity.Generic()

class BlockTag:
    def __init__(self, *args):
        self._blocks = args

class Block:
    """
    This class is a representation of a block

    It maintains state by assuming that the block is not modified outside of the
    behavior defined in this script

    All blocks are uniquely identified by their Position, which contains
    coordinates and dimension
    """
    class Generic:
        pass
    class Dirt(Generic):
        pass

class Particle:
    class Emitter:
        pass

class Enchantment:
    pass

class Effect:
    pass

class Item:
    pass
class BlockItem(Item):
    pass
class Armor(Item):
    pass
class Helmet(Armor):
    pass
class Chestplate(Armor):
    pass
class Leggings(Armor):
    pass
class Boots(Armor):
    pass
class LeatherArmor(Armor):
    pass
class LeatherHelmet(Helmet, LeatherArmor):
    pass
class LeatherChestplate(Chestplate, LeatherArmor):
    pass
class LeatherLeggings(Leggings, LeatherArmor):
    pass
class LeatherBoots(Boots, LeatherArmor):
    pass
class Tool(Item):
    class Durability:
        NETHERITE_HELMET = 407
        NETHERITE_CHESTPLATE = 592
        NETHERITE_LEGGINGS = 555
        NETHERITE_BOOTS = 481
        NETHERITE_TOOL = 2031

    class EffectiveMaterials:
        DIRT = 0
        STONE = 1
        WOOD = 2
        PLANT_MATTER = 3
        COBWEB = 4
        NONE=5
    pass
class Sword(Tool):
    pass
class Axe(Tool):
    pass
class Shovel(Tool):
    pass
class Hoe(Tool):
    pass
class Pickace(Tool):
    pass
class Bow(Tool):
    pass
class FlintAndSteel(Tool):
    pass
class CarrotOnAStick(Tool):
    pass
class Shears(Tool):
    pass
class Shield(Tool):
    pass
class Bow(Tool):
    pass
class Trident(Tool):
    pass
class Crossbow(Tool):
    pass
class WarpedFungusOnAStick(Tool):
    pass

class Color:
    BLACK = 'black'

    def __init__(self, r, g, b):
        pass
    def __init__(self, hex_str):
        pass