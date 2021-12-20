from enum import Enum
from typing import List

from pyspecde.spectrum_api_wrapper import _decode_bitmap_using_enum
from spectrum_gmbh.regs import (
    SPCM_FEAT_MULTI,
    SPCM_FEAT_GATE,
    SPCM_FEAT_DIGITAL,
    SPCM_FEAT_TIMESTAMP,
    SPCM_FEAT_STARHUB6_EXTM,
    SPCM_FEAT_STARHUB8_EXTM,
    SPCM_FEAT_STARHUB4,
    SPCM_FEAT_STARHUB5,
    SPCM_FEAT_STARHUB16_EXTM,
    SPCM_FEAT_STARHUB8,
    SPCM_FEAT_STARHUB16,
    SPCM_FEAT_ABA,
    SPCM_FEAT_BASEXIO,
    SPCM_FEAT_AMPLIFIER_10V,
    SPCM_FEAT_STARHUBSYSMASTER,
    SPCM_FEAT_DIFFMODE,
    SPCM_FEAT_SEQUENCE,
    SPCM_FEAT_AMPMODULE_10V,
    SPCM_FEAT_STARHUBSYSSLAVE,
    SPCM_FEAT_NETBOX,
    SPCM_FEAT_REMOTESERVER,
    SPCM_FEAT_SCAPP,
    SPCM_FEAT_CUSTOMMOD_MASK,
    SPCM_FEAT_EXTFW_SEGSTAT,
    SPCM_FEAT_EXTFW_SEGAVERAGE,
    SPCM_FEAT_EXTFW_BOXCAR,
)


class CardFeature(Enum):
    """Enum representing the possible features of all Spectrum devices. A list of features can be read from a device
    using the feature_list property. See the Spectrum documentation for descriptions of each of the features."""

    SPCM_FEAT_MULTI = SPCM_FEAT_MULTI
    SPCM_FEAT_GATE = SPCM_FEAT_GATE
    SPCM_FEAT_DIGITAL = SPCM_FEAT_DIGITAL
    SPCM_FEAT_TIMESTAMP = SPCM_FEAT_TIMESTAMP
    SPCM_FEAT_STARHUB6_EXTM = SPCM_FEAT_STARHUB6_EXTM
    SPCM_FEAT_STARHUB8_EXTM = SPCM_FEAT_STARHUB8_EXTM
    SPCM_FEAT_STARHUB4 = SPCM_FEAT_STARHUB4
    SPCM_FEAT_STARHUB5 = SPCM_FEAT_STARHUB5
    SPCM_FEAT_STARHUB16_EXTM = SPCM_FEAT_STARHUB16_EXTM
    SPCM_FEAT_STARHUB8 = SPCM_FEAT_STARHUB8
    SPCM_FEAT_STARHUB16 = SPCM_FEAT_STARHUB16
    SPCM_FEAT_ABA = SPCM_FEAT_ABA
    SPCM_FEAT_BASEXIO = SPCM_FEAT_BASEXIO
    SPCM_FEAT_AMPLIFIER_10V = SPCM_FEAT_AMPLIFIER_10V
    SPCM_FEAT_STARHUBSYSMASTER = SPCM_FEAT_STARHUBSYSMASTER
    SPCM_FEAT_DIFFMODE = SPCM_FEAT_DIFFMODE
    SPCM_FEAT_SEQUENCE = SPCM_FEAT_SEQUENCE
    SPCM_FEAT_AMPMODULE_10V = SPCM_FEAT_AMPMODULE_10V
    SPCM_FEAT_STARHUBSYSSLAVE = SPCM_FEAT_STARHUBSYSSLAVE
    SPCM_FEAT_NETBOX = SPCM_FEAT_NETBOX
    SPCM_FEAT_REMOTESERVER = SPCM_FEAT_REMOTESERVER
    SPCM_FEAT_SCAPP = SPCM_FEAT_SCAPP
    SPCM_FEAT_CUSTOMMOD_MASK = SPCM_FEAT_CUSTOMMOD_MASK


def decode_card_features(value: int) -> List[CardFeature]:
    possibe_values = [feature.value for feature in CardFeature]
    return [CardFeature(found_value) for found_value in _decode_bitmap_using_enum(value, possibe_values)]


class AdvancedCardFeature(Enum):
    """Enum representing the possible advanced features of all Spectrum devices. A list of features can be read from a
    device using the feature_list property. See the Spectrum documentation for descriptions of each of the features.
    """

    SPCM_FEAT_EXTFW_SEGSTAT = SPCM_FEAT_EXTFW_SEGSTAT
    SPCM_FEAT_EXTFW_SEGAVERAGE = SPCM_FEAT_EXTFW_SEGAVERAGE
    SPCM_FEAT_EXTFW_BOXCAR = SPCM_FEAT_EXTFW_BOXCAR


def decode_advanced_card_features(value: int) -> List[AdvancedCardFeature]:
    possible_values = [feature.value for feature in AdvancedCardFeature]
    return [AdvancedCardFeature(found_value) for found_value in _decode_bitmap_using_enum(value, possible_values)]
