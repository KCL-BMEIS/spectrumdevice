from typing import Optional, Sequence

from numpy import int16
from numpy.typing import NDArray

from spectrum_gmbh.regs import SPC_MIINST_CHPERMODULE, SPC_MIINST_MODULES
from spectrumdevice import AbstractSpectrumCard
from spectrumdevice.devices.awg.abstract_spectrum_awg import AbstractSpectrumAWG
from spectrumdevice.devices.awg.awg_channel import SpectrumAWGAnalogChannel
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGAnalogChannelInterface
from spectrumdevice.settings import TransferBuffer
from spectrumdevice.settings.transfer_buffer import (
    BufferDirection,
    BufferType,
    set_transfer_buffer,
    transfer_buffer_factory,
)


class SpectrumAWGCard(AbstractSpectrumCard[SpectrumAWGAnalogChannelInterface], AbstractSpectrumAWG):
    def _init_channels(self) -> Sequence[SpectrumAWGAnalogChannelInterface]:
        num_modules = self.read_spectrum_device_register(SPC_MIINST_MODULES)
        num_channels_per_module = self.read_spectrum_device_register(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return tuple([SpectrumAWGAnalogChannel(n, self) for n in range(total_channels)])

    def transfer_waveform(self, waveform: NDArray[int16]) -> None:
        buffer = transfer_buffer_factory(
            buffer_type=BufferType.SPCM_BUF_DATA,
            direction=BufferDirection.SPCM_DIR_PCTOCARD,
            size_in_samples=len(waveform),
        )
        buffer.data_array[:] = waveform
        self.define_transfer_buffer((buffer,))

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
