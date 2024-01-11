import logging
from typing import Optional, Sequence

from numpy import int16
from numpy.typing import NDArray

from spectrum_gmbh.regs import SPC_MIINST_CHPERMODULE, SPC_MIINST_MODULES, TYP_SERIESMASK, TYP_M2PEXPSERIES, SPC_MEMSIZE
from spectrumdevice.devices.abstract_device import AbstractSpectrumCard
from spectrumdevice.devices.awg.abstract_spectrum_awg import AbstractSpectrumAWG
from spectrumdevice.devices.awg.awg_channel import SpectrumAWGAnalogChannel, SpectrumAWGIOLine
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGAnalogChannelInterface, SpectrumAWGIOLineInterface
from spectrumdevice.settings import TransferBuffer
from spectrumdevice.settings.card_dependent_properties import get_memsize_step_size
from spectrumdevice.settings.transfer_buffer import (
    BufferDirection,
    BufferType,
    set_transfer_buffer,
    transfer_buffer_factory,
)

logger = logging.getLogger(__name__)


class SpectrumAWGCard(
    AbstractSpectrumCard[SpectrumAWGAnalogChannelInterface, SpectrumAWGIOLineInterface], AbstractSpectrumAWG
):
    def _init_analog_channels(self) -> Sequence[SpectrumAWGAnalogChannelInterface]:
        num_modules = self.read_spectrum_device_register(SPC_MIINST_MODULES)
        num_channels_per_module = self.read_spectrum_device_register(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return tuple([SpectrumAWGAnalogChannel(channel_number=n, parent_device=self) for n in range(total_channels)])

    def _init_io_lines(self) -> Sequence[SpectrumAWGIOLineInterface]:
        if (self.model_number.value & TYP_SERIESMASK) == TYP_M2PEXPSERIES:
            return tuple([SpectrumAWGIOLine(channel_number=n, parent_device=self) for n in range(4)])
        else:
            raise NotImplementedError("Don't know how many IO lines other types of card have. Only M2P series.")

    def transfer_waveform(self, waveform: NDArray[int16]) -> None:
        buffer = transfer_buffer_factory(
            buffer_type=BufferType.SPCM_BUF_DATA,
            direction=BufferDirection.SPCM_DIR_PCTOCARD,
            size_in_samples=len(waveform),
            bytes_per_sample=self.bytes_per_sample,
        )
        if len(waveform) < 16:
            raise ValueError("Waveform must be at least 16 samples long")
        buffer.data_array[:] = waveform
        self.define_transfer_buffer((buffer,))
        step_size = get_memsize_step_size(self._model_number)
        remainder = len(waveform) % step_size
        if remainder > 0:
            logger.warning(
                "Waveform length is not a multiple of 8 samples. Waveform in card memory will be zero-padded"
                " to the next multiple of 8."
            )
        coerced_mem_size = len(waveform) if remainder == 0 else len(waveform) + (step_size - remainder)
        self.write_to_spectrum_device_register(SPC_MEMSIZE, coerced_mem_size)
        self.start_transfer()
        self.wait_for_transfer_chunk_to_complete()

    def define_transfer_buffer(self, buffer: Optional[Sequence[TransferBuffer]] = None) -> None:
        """Provide a `TransferBuffer` object for transferring samples to the card. This is called internally when
        transfer_waveform is used to send a single waveform to the card.

        Args:
            buffer (Optional[List[`TransferBuffer`]]): A length-1 list containing a pre-constructed
                `TransferBuffer`  The buffer should have buffer_type=BufferType.SPCM_BUF_DATA and
                BufferDirection.SPCM_DIR_PCTOCARD. The size of the buffer should be chosen according to the
                length of the data to transfer.
        """
        if buffer is None:
            raise ValueError(
                "You must provide a preconfigured buffer for transferring samples to an AWG because the"
                "buffer size cannot be inferred."
            )
        self._transfer_buffer = buffer[0]
        set_transfer_buffer(self._handle, self._transfer_buffer)
