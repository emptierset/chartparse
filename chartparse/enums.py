import enum

from chartparse.util import AllValuesGettableEnum


@enum.unique
class Difficulty(AllValuesGettableEnum):
    EXPERT = "Expert"
    HARD = "Hard"
    MEDIUM = "Medium"
    EASY = "Easy"


@enum.unique
class Instrument(AllValuesGettableEnum):
    GUITAR = "Single"
    GUITAR_COOP = "DoubleGuitar"
    BASS = "DoubleBass"
    RHYTHM = "DoubleRhythm"
    KEYS = "Keyboard"
    DRUMS = "Drums"
    GHL_GUITAR = "GHLGuitar" # Guitar (Guitar Hero: Live)
    GHL_BASS = "GHLBass"     # Bass (Guitar Hero: Live)


class Note(enum.Enum):
    P     = bytearray((0, 0, 0, 0, 0))
    G     = bytearray((1, 0, 0, 0, 0))
    GR    = bytearray((1, 1, 0, 0, 0))
    GY    = bytearray((1, 0, 1, 0, 0))
    GB    = bytearray((1, 0, 0, 1, 0))
    GO    = bytearray((1, 0, 0, 0, 1))
    GRY   = bytearray((1, 1, 1, 0, 0))
    GRB   = bytearray((1, 1, 0, 1, 0))
    GRO   = bytearray((1, 1, 0, 0, 1))
    GYB   = bytearray((1, 0, 1, 1, 0))
    GYO   = bytearray((1, 0, 1, 0, 1))
    GBO   = bytearray((1, 0, 0, 1, 1))
    GRYB  = bytearray((1, 1, 1, 1, 0))
    GRYO  = bytearray((1, 1, 1, 0, 1))
    GRBO  = bytearray((1, 1, 0, 1, 1))
    GYBO  = bytearray((1, 0, 1, 1, 1))
    GRYBO = bytearray((1, 1, 1, 1, 1))
    R     = bytearray((0, 1, 0, 0, 0))
    RY    = bytearray((0, 1, 1, 0, 0))
    RB    = bytearray((0, 1, 0, 1, 0))
    RO    = bytearray((0, 1, 0, 0, 1))
    RYB   = bytearray((0, 1, 1, 1, 0))
    RYO   = bytearray((0, 1, 1, 0, 1))
    RBO   = bytearray((0, 1, 0, 1, 1))
    RYBO  = bytearray((0, 1, 1, 1, 1))
    Y     = bytearray((0, 0, 1, 0, 0))
    YB    = bytearray((0, 0, 1, 1, 0))
    YO    = bytearray((0, 0, 1, 0, 1))
    YBO   = bytearray((0, 0, 1, 1, 1))
    B     = bytearray((0, 0, 0, 1, 0))
    BO    = bytearray((0, 0, 0, 1, 1))
    O     = bytearray((0, 0, 0, 0, 1))
    # Aliases
    OPEN                         = bytearray((0, 0, 0, 0, 0))
    GREEN                        = bytearray((1, 0, 0, 0, 0))
    GREEN_RED                    = bytearray((1, 1, 0, 0, 0))
    GREEN_YELLOW                 = bytearray((1, 0, 1, 0, 0))
    GREEN_BLUE                   = bytearray((1, 0, 0, 1, 0))
    GREEN_ORANGE                 = bytearray((1, 0, 0, 0, 1))
    GREEN_RED_YELLOW             = bytearray((1, 1, 1, 0, 0))
    GREEN_RED_BLUE               = bytearray((1, 1, 0, 1, 0))
    GREEN_RED_ORANGE             = bytearray((1, 1, 0, 0, 1))
    GREEN_YELLOW_BLUE            = bytearray((1, 0, 1, 1, 0))
    GREEN_YELLOW_ORANGE          = bytearray((1, 0, 1, 0, 1))
    GREEN_BLUE_ORANGE            = bytearray((1, 0, 0, 1, 1))
    GREEN_RED_YELLOW_BLUE        = bytearray((1, 1, 1, 1, 0))
    GREEN_RED_YELLOW_ORANGE      = bytearray((1, 1, 1, 0, 1))
    GREEN_RED_BLUE_ORANGE        = bytearray((1, 1, 0, 1, 1))
    GREEN_YELLOW_BLUE_ORANGE     = bytearray((1, 0, 1, 1, 1))
    GREEN_RED_YELLOW_BLUE_ORANGE = bytearray((1, 1, 1, 1, 1))
    RED                          = bytearray((0, 1, 0, 0, 0))
    RED_YELLOW                   = bytearray((0, 1, 1, 0, 0))
    RED_BLUE                     = bytearray((0, 1, 0, 1, 0))
    RED_ORANGE                   = bytearray((0, 1, 0, 0, 1))
    RED_YELLOW_BLUE              = bytearray((0, 1, 1, 1, 0))
    RED_YELLOW_ORANGE            = bytearray((0, 1, 1, 0, 1))
    RED_BLUE_ORANGE              = bytearray((0, 1, 0, 1, 1))
    RED_YELLOW_BLUE_ORANGE       = bytearray((0, 1, 1, 1, 1))
    YELLOW                       = bytearray((0, 0, 1, 0, 0))
    YELLOW_BLUE                  = bytearray((0, 0, 1, 1, 0))
    YELLOW_ORANGE                = bytearray((0, 0, 1, 0, 1))
    YELLOW_BLUE_ORANGE           = bytearray((0, 0, 1, 1, 1))
    BLUE                         = bytearray((0, 0, 0, 1, 0))
    BLUE_ORANGE                  = bytearray((0, 0, 0, 1, 1))
    ORANGE                       = bytearray((0, 0, 0, 0, 1))


class NoteTrackIndex(AllValuesGettableEnum):
    G      = 0
    R      = 1
    Y      = 2
    B      = 3
    O      = 4
    P      = 7
    FORCED = 5
    TAP    = 6
    # Aliases
    GREEN  = 0
    RED    = 1
    YELLOW = 2
    BLUE   = 3
    ORANGE = 4
    OPEN   = 7

