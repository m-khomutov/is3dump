class Version:
    @staticmethod
    def Mpeg4():
        return Version(0)
    @staticmethod
    def Mpeg2():
        return Version(1)
    def __init__(self, value):
        self._value=value & 1
    def __int__(self):
        return self._value & 1

class AdtsHeader:
    def __init__(self, **kwargs):
        config=kwargs.get('config', 0)
        self.profile=(config >> 11) & 0x1f
        self.freqidx=(config>>7) & 0xf
        self.channels=(config>>3) & 0xf
        self.version=kwargs.get('version',Version.Mpeg4())
        self.noprotection=kwargs.get('noProtection',True)
    def encode(self, framelen):
        framelen += 7
        rc=bytearray()
        rc.extend(0xff.to_bytes(1, byteorder='big'))
        rc.extend((0xf0 |
                   (int(self.version) << 3) |
                   (0x00 << 1) |
                   (self.noprotection)).to_bytes(1, byteorder='big'))
        rc.extend((((self.profile-1) << 6) |
                    (self.freqidx << 2) |
                    (0x00 << 1) |
                    (self.channels >> 2)).to_bytes(1, byteorder='big'))
        rc.extend(((self.channels << 6) |
                   (0x00 << 2) |
                   ((framelen >> 11) & 3)).to_bytes(1, byteorder='big'))
        rc.extend((framelen >> 3).to_bytes(1, byteorder='big'))
        rc.extend((((framelen & 7) << 5) | 0x1f).to_bytes(1, byteorder='big'))
        rc.extend(0xfc.to_bytes(1, byteorder='big'))
        return rc
