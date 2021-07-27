"""Module describes the frames natively supported by ID3v2.4.0,
   which is a revised version of the ID3v2 informal standard [ID3v2.3.0]
   version 2.3.0. The ID3v2 offers a flexible way of storing audio meta
   information within audio file itself. The information may be
   technical information, such as equalisation curves, as well as title,
   performer, copyright etc."""


class Frame:
    """Frame natively supported by ID3v2.4.0"""
    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self._body = kwargs.get('content', '')
        self._flags = kwargs.get('flags', 0)
        self._size = 11+len(self._body)

    def __len__(self):
        return self._size

    def encode(self):
        """Returns frame as bytearray ready to be saved to file"""
        encoded = bytearray()
        encoded.extend(self._id.encode())
        encoded.extend((len(self._body)+1).to_bytes(4, byteorder='big'))
        encoded.extend(self._flags.to_bytes(2, byteorder='big'))
        encoded.extend(0x00.to_bytes(1, byteorder='big'))
        encoded.extend(self._body.encode())
        return encoded


class Header:
    """Frame metadata"""
    def __init__(self, **kwargs):
        self._version = kwargs.get('version', 3)
        self._flags = kwargs.get('flags', 0)
        self.size = 0

    @property
    def flags(self):
        """returns metadata flags field"""
        return self._flags

    @flags.setter
    def flags(self, value):
        """sets metadata flags field"""
        self._flags = value

    def encode(self):
        """Returns frame metadata as bytearray ready to be saved to file"""
        encoded = bytearray()
        encoded.extend(0x494433.to_bytes(3, byteorder='big'))  # ID3v2/file identifier "ID3"
        encoded.extend(self._version.to_bytes(1, byteorder='big'))
        encoded.extend(0x00.to_bytes(1, byteorder='big'))  # subversion
        encoded.extend(self._flags.to_bytes(1, byteorder='big'))
        encoded.extend(self._encode_size())
        return encoded

    def _encode_size(self):
        """Returns frame full size in id3 format as bytearray ready to be saved to file"""
        encoded = bytearray()
        encoded.extend(((self.size >> 21) & 0x7f).to_bytes(1, byteorder='big'))
        encoded.extend(((self.size >> 14) & 0x7f).to_bytes(1, byteorder='big'))
        encoded.extend(((self.size >> 7) & 0x7f).to_bytes(1, byteorder='big'))
        encoded.extend(((self.size >> 0) & 0x7f).to_bytes(1, byteorder='big'))
        return encoded


class Tag:
    """id3 tag. Contains metadata ans a set of ID3v2 frames"""
    def __init__(self, **kwargs):
        self._header = Header(**kwargs)
        self._frames = []

    def add_frame(self, frame):
        """ads ID3v3 frame to tag"""
        self._frames.append(frame)
        self._header.size += len(frame)

    def encode(self):
        """Returns tag as bytearray ready to be saved to file"""
        encoded = self._header.encode()
        for frame in self._frames:
            encoded.extend(frame.encode())
        return encoded
