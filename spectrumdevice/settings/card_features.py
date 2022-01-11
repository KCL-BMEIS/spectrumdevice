"""Provides Enums defining the possible values a device will return when queried about its features, and functions for
decoding the received values into lists of features."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from enum import Enum
from typing import List

from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints
from spectrum_gmbh.regs import (
    SPCM_FEAT_MULTI,
    SPCM_FEAT_GATE,
    SPCM_FEAT_DIGITAL,
    SPCM_FEAT_TIMESTAMP,
    SPCM_FEAT_STARHUB4,
    SPCM_FEAT_STARHUB8,
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

# Devices return same value for SPCM_FEAT_STARHUB4, SPCM_FEAT_STARHUB4, SPCM_FEAT_STARHUB6_EXTM and
# SPCM_FEAT_STARHUB8_EXTM card features
SPCM_FEAT_STARHUB_4_5_6EXTM_8EXTM = SPCM_FEAT_STARHUB4  # Devices return same value for SPCM_FEAT_STARHUB4

# Devices return same value for SPCM_FEAT_STARHUB8, SPCM_FEAT_STARHUB16 and SPCM_FEAT_STARHUB16_EXTM card features
SPCM_FEAT_STARHUB_8_16_16EXTM = SPCM_FEAT_STARHUB8


class CardFeature(Enum):
    """Enum representing the possible features of all Spectrum devices. A list of features can be read from a device
    using the feature_list property. See the Spectrum documentation for descriptions of each of the features."""

    SPCM_FEAT_MULTI = SPCM_FEAT_MULTI
    SPCM_FEAT_GATE = SPCM_FEAT_GATE
    SPCM_FEAT_DIGITAL = SPCM_FEAT_DIGITAL
    SPCM_FEAT_TIMESTAMP = SPCM_FEAT_TIMESTAMP
    SPCM_FEAT_STARHUB_4_5_6EXTM_8EXTM = SPCM_FEAT_STARHUB_4_5_6EXTM_8EXTM
    SPCM_FEAT_STARHUB_8_16_16EXTM = SPCM_FEAT_STARHUB_8_16_16EXTM
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
    """Converts the integer value received by a Spectrum device when queried about its features into a list of
    CardFeatures."""
    possibe_values = [feature.value for feature in CardFeature]
    return [CardFeature(found_value) for found_value in decode_bitmap_using_list_of_ints(value, possibe_values)]


class AdvancedCardFeature(Enum):
    """Enum representing the possible advanced features of all Spectrum devices. A list of features can be read from a
    device using the feature_list property. See the Spectrum documentation for descriptions of each of the features.
    """

    SPCM_FEAT_EXTFW_SEGSTAT = SPCM_FEAT_EXTFW_SEGSTAT
    SPCM_FEAT_EXTFW_SEGAVERAGE = SPCM_FEAT_EXTFW_SEGAVERAGE
    SPCM_FEAT_EXTFW_BOXCAR = SPCM_FEAT_EXTFW_BOXCAR


def decode_advanced_card_features(value: int) -> List[AdvancedCardFeature]:
    """Converts the integer value received by a Spectrum device when queried about its advanced features into a list of
    AdvancedCardFeatures."""
    possible_values = [feature.value for feature in AdvancedCardFeature]
    return [
        AdvancedCardFeature(found_value) for found_value in decode_bitmap_using_list_of_ints(value, possible_values)
    ]
