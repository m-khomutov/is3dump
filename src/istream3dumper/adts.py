"""Module describes aac audio data transport stream header"""
from enum import IntFlag


class Version(IntFlag):
    """Header ID"""
    MPEG4 = 0
    MPEG2 = 1


class Header:
    """Audio data transport stream header"""
    _frequencies = [96000, 88200, 64000, 48000, 44100, 32000,
                    24000, 22050, 16000, 12000, 11025, 8000, 7350]

    def __init__(self, **kwargs):
        config = kwargs.get('config', 0)
        self._profile = (config >> 11) & 0x1f
        self._freq_idx = (config >> 7) & 0xf
        self._channels = (config >> 3) & 0xf
        self._version = kwargs.get('version', Version.MPEG4)
        self._protection_absent = kwargs.get('protection_absent', True)

    @property
    def frequency(self):
        """Returns header frequency"""
        for index, frequency in enumerate(self._frequencies):
            if index == self._freq_idx:
                return frequency
        return 0

    @property
    def channels(self):
        """Returns header channels"""
        return self._channels

    def encode(self, frame_len):
        """Returns header as bytearray ready to be saved to file"""
        frame_len += 7
        result = bytearray()
        result.extend(0xff.to_bytes(1, byteorder='big'))
        result.extend((0xf0 |
                      (self._version << 3) |
                      (0x00 << 1) |
                       self._protection_absent).to_bytes(1, byteorder='big'))
        result.extend((((self._profile-1) << 6) |
                      (self._freq_idx << 2) |
                      (0x00 << 1) |
                      (self._channels >> 2)).to_bytes(1, byteorder='big'))
        result.extend(((self._channels << 6) |
                      (0x00 << 2) |
                      ((frame_len >> 11) & 3)).to_bytes(1, byteorder='big'))
        result.extend((frame_len >> 3).to_bytes(1, byteorder='big'))
        result.extend((((frame_len & 7) << 5) | 0x1f).to_bytes(1, byteorder='big'))
        result.extend(0xfc.to_bytes(1, byteorder='big'))
        return result
