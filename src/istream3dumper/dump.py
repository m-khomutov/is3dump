"""Dumps stream from IStream3 channel by id"""
import getopt
import os
import sys
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
    def show_params():
        """Shows command line parameters"""
        print("params:\n\t-c(--channel) path to channel directory (req.)\n\t"
              "-i(--id) stream id (def. 0)\n\t"
              "-d(--dump) path to dumpfile(def. ./channel_id)\n\t"
              "-o(--override) override existing file (def. exit without overriding)\n\t"
              "-v(--verb) be verbose - show index blocks\n\t"
              "-h(--help) this help")
        sys.exit()

    @staticmethod
    def get_params(argv):
        """Returns command line parameters"""
        channel_path = ''
        stream_id = 0
        dump_path = ''
        is_verbose = False
        override = False
        opts = ()
        try:
            opts, remainder = getopt.getopt(argv,
                                            "c:i:d:ovh",
                                            ["channel=", "id=", "dump=",
                                             "override", "verb", "help"])
            if len(remainder):
                raise getopt.GetoptError('invalid options: ' + ' '.join(remainder))
        except getopt.GetoptError as opt_error:
            print(opt_error)
            Dump.show_params()
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                Dump.show_params()
            elif opt in ('-c', '--channel'):
                channel_path = arg
            elif opt in ('-i', '--id'):
                stream_id = int(arg)
            elif opt in ('-d', '--dump'):
                dump_path = arg
            elif opt in ('-o', '--override'):
                override = True
            elif opt in ('-v', '--verb'):
                is_verbose = True
        if len(channel_path) == 0:
            Dump.show_params()
        return channel_path, stream_id, dump_path, override, is_verbose

    @staticmethod
    def make(argv):
        """Creates Dumper object according to encoding name"""
        channel_path, stream_id, dump_path, override, verb = Dump.get_params(argv)
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
                                 config=int(channel.search(u'fmtp').split('config=')[1][:4], 16),
                                 stream_id=stream_id,
                                 verbose=verb)
            elif enc == 'h264':
                dumper = AnnexBDump(dump_path, channel,
                                    channel_id=channel_id,
                                    stream_id=stream_id,
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
            for blk in Index(chunk):
                if blk.stream_id == self._stream_id and blk.offset < len(data):
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


class AnnexBDump(Dump):
    """Dumps h264 stream with annexB divider"""
    _divider = b'\x00\x00\x00\x01'

    def _write_block(self, file, data):
        file.write(self._divider)
        file.write(data)
