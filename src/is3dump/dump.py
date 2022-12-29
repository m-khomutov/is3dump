"""Dumps stream from IStream3 channel by id"""
import os
import sys
from enum import IntEnum
from .id3 import Tag, Frame
from .channel import Index, Channel, Data
from .adts import Header as AudioDataTsHeader


def id3(cls):
    """Decorator to add id3 tag to dump file"""
    class Id3Inserter(cls):
        """Id3 tag inserter to dump file"""
        _tag = None

        @property
        def tag(self):
            """Id3 tag getter"""
            return self._tag

        def write(self):
            """Redefined dump function of base class to add id3 tag to dump file"""
            with open(super().filename, 'wb') as file:
                self._tag = Tag()
                self._tag.add_frame(Frame(id='TPUB', content='IStream'))
                self._tag.add_frame(Frame(id='TIT2', content=super().channel_id))
                file.write(self._tag.encode())
                super().write_chunks(file)
    return Id3Inserter


@id3
class Dump:
    """IStream3 channel dumper - dumps a channel stream by id"""
    @staticmethod
    def make(*params):
        """Creates Dumper object according to encoding name"""
        channel_path, stream_id, dump_path, dump_range, override, verb, *left = params
        channel_id = channel_path.split('/')[-1]
        try:
            channel = Channel(channel_path, stream_id)
            enc = channel.search('encoding')
            if len(dump_path) == 0:
                dump_path = channel_id + '.' + enc
            if not override and os.path.exists(dump_path):
                raise IOError(dump_path)
            dumper = None
            if enc == 'aac':
                dumper = AacDump(dump_path, channel,
                                 channel_id=channel_id,
                                 config=int(channel.search('fmtp').split('config=')[1][:4], 16),
                                 stream_id=stream_id,
                                 range=dump_range,
                                 verbose=verb)
            elif enc == 'h264':
                dumper = AnnexBDump(dump_path, channel,
                                    channel_id=channel_id,
                                    stream_id=stream_id,
                                    range=dump_range,
                                    verbose=verb)
            return dumper
        except IOError as io_error:
            print('invalid path: ', io_error)
            sys.exit()

    def __init__(self, filename, channel, **kwargs):
        self._filename = filename
        self._channel = channel
        self._channel_id = kwargs.get('channel_id', '')
        self._stream_id = kwargs.get('stream_id', 0)
        dump_range = kwargs.get('range', ())
        self._begin = dump_range[0] if len(dump_range) > 0 else 0
        self._end = dump_range[1] if len(dump_range) > 1 else 0
        self._verbose = kwargs.get('verbose', False)

    @property
    def channel_id(self):
        """Channel ID field setter"""
        return self._channel_id

    @property
    def filename(self):
        """Filename field setter"""
        return self._filename

    def write(self):
        """abstract method redefined in id3 decorator with main goal to call write_chunks method"""

    def _write_block(self, file, data):
        pass

    def write_chunks(self, file):
        """dumps stream chunks from channel"""
        for chunk in self._channel.chunks:
            data = Data(chunk.rstrip(".idx"))
            for blk in Index(chunk, self._end):
                if blk.stream_id == self._stream_id and blk.offset < len(data):
                    if blk.timestamp >= self._begin:
                        if self._verbose:
                            print('{}'.format(blk))
                        self._write_block(file, data.frame(blk))


class AacDump(Dump):
    """Dumps aac stream with audio data transport stream header"""
    def __init__(self, filename, channel, **kwargs):
        super().__init__(filename, channel, **kwargs)
        self._config = kwargs.get('config', 0)

    def _write_block(self, file, data):
        file.write(AudioDataTsHeader(config=self._config).encode(len(data)))
        file.write(data)


class UnitType(IntEnum):
    """Video unit type enumeration"""
    IDR = 5
    SPS = 7
    PPS = 8


class AnnexBDump(Dump):
    """Dumps h264 stream with annexB divider"""
    _divider = b'\x00\x00\x00\x01'
    _sps_dumped, _pps_dumped = False, False

    def _write_block(self, file, data):
        slice_type = int(data[0] & 0x1f)
        if slice_type == UnitType.SPS:
            self._sps_dumped = True
        elif slice_type == UnitType.PPS:
            self._pps_dumped = True
        if slice_type > UnitType.IDR or self._ready_to_write():
            file.write(self._divider)
            file.write(data)

    def _ready_to_write(self):
        """Checks if block can be dumped"""
        return self._sps_dumped and self._pps_dumped


def dump():
    if (dumper := Dump.make(sys.argv[1:])) is not None:
        dumper.write()
