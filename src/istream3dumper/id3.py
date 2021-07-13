class Frame:
    def __init__(self, **kwargs):
        self.id=kwargs.get('id')
        self.body=kwargs.get('content','')
        self.flags=kwargs.get('flags',0)
        self.size=11+len(self.body)
    def encode(self):
        rc=bytearray()
        rc.extend(self.id.encode())
        rc.extend((len(self.body)+1).to_bytes(4,byteorder='big'))
        rc.extend(self.flags.to_bytes(2,byteorder='big'))
        rc.extend(0x00.to_bytes(1, byteorder='big'))
        rc.extend(self.body.encode())
        return rc

class Header:
    def __init__(self, **kwargs):
        self._version=kwargs.get('version', 3)
        self._flags = kwargs.get('flags', 0)
        self._size=0
    def encode(self):
        rc=bytearray()
        rc.extend(0x494433.to_bytes(3, byteorder='big'))  # ID3v2/file identifier "ID3"
        rc.extend(self._version.to_bytes(1, byteorder='big'))
        rc.extend(0x00.to_bytes(1, byteorder='big'))  # subversion
        rc.extend(self._flags.to_bytes(1,byteorder='big'))
        rc.extend(self.__encode_size())
        return rc
    def __encode_size(self):
        rc=bytearray()
        rc.extend(((self._size >> 21) & 0x7f).to_bytes(1,byteorder='big'))
        rc.extend(((self._size >> 14) & 0x7f).to_bytes(1,byteorder='big'))
        rc.extend(((self._size >> 7) & 0x7f).to_bytes(1,byteorder='big'))
        rc.extend(((self._size >> 0) & 0x7f).to_bytes(1,byteorder='big'))
        return rc

class Tag:
    def __init__(self, **kwargs):
        self.header=Header(**kwargs)
        self.frames=[]
    def add_frame(self, frame):
        self.frames.append(frame)
        self.header._size += frame.size
    def encode(self):
        rc=self.header.encode()
        for fr in self.frames:
            rc.extend(fr.encode())
        return rc
