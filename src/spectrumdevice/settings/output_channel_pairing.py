from enum import Enum

from spectrum_gmbh.regs import SPC_DIFF0, SPC_DIFF2, SPC_DIFF4, SPC_DIFF6, SPC_DOUBLEOUT0, SPC_DOUBLEOUT2


class ChannelPairingMode:
    SINGLE: 0
    """No channel pairing"""
    DOUBLE: 1
    """Odd-numbered channel's output is identical to even-numbered channel's output. """
    DIFFERENTIAL: 2
    """Odd-numbered channel's output is inverse of even-numbered channel's output. """


class ChannelPair(Enum):
    CHANNEL_0_AND_1: 0
    CHANNEL_2_AND_3: 2
    CHANNEL_4_AND_5: 4
    CHANNEL_6_AND_7: 6


DIFFERENTIAL_CHANNEL_PAIR_COMMANDS = {
    ChannelPair.CHANNEL_0_AND_1: SPC_DIFF0,
    ChannelPair.CHANNEL_2_AND_3: SPC_DIFF2,
    ChannelPair.CHANNEL_4_AND_5: SPC_DIFF4,
    ChannelPair.CHANNEL_6_AND_7: SPC_DIFF6,
}

DOUBLING_CHANNEL_PAIR_COMMANDS = {
    ChannelPair.CHANNEL_0_AND_1: SPC_DOUBLEOUT0,
    ChannelPair.CHANNEL_2_AND_3: SPC_DOUBLEOUT2,
}
