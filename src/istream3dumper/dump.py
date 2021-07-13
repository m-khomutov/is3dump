import getopt
import os
import sys
from .id3 import Tag,Frame 
from .adts import AdtsHeader 
from .channel import Index,Channel,Data

class Dump:
    @staticmethod
    def showParams():
        print("params:\n\t-c(--channel) path to channel directory (req.)\n\t"
              "-i(--id) stream id (def. 0)\n\t"
              "-d(--dump) path to dumpfile(def. ./channelid)\n\t"
              "-h(--help) this help")
        sys.exit()
    def getParams(argv):
        try:
            opts,args=getopt.getopt(argv, "c:i:d:h", ["channel=", "id=", "dump=", "help"])
        except getopt.GetoptError as e:
            print(e)
            sys.exit()
        chanpath = ''
        streamid = 0
        dumppath = ''
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                Dump.showParams()
            elif opt in ('-c', '--channel'):
                chanpath = arg
            elif opt in ('-i', '--id'):
                streamid = int(arg)
            elif opt in ('-d', '--dump'):
                dumppath = arg
        if len(chanpath) == 0:
            Dump.showParams()
        return (chanpath,streamid,dumppath)

    @staticmethod
    def make(argv):
        channel_path,stream_id,dump_path=Dump.getParams(argv)
        channel_id=channel_path.split('/')[-1]
        try:
            chan=Channel(channel_path, stream_id)
            enc=chan.search('encoding')
            if enc=='aac':
                if len(dump_path)==0:
                    dump_path=channel_id+'.aac'
                return AacDump(dump_path, chan,
                               channelid=channel_id,
                               config=int(chan.search('fmtp').split('config=')[1][:4], 16),
                               streamid=stream_id)
            elif enc=='h264':
                if len(dump_path)==0:
                    dump_path=channel_id+'.264'
                return AnnexBDump(dump_path, chan,
                                  streamid=stream_id)
        except IOError as e:
            print('invalid path: ', e)
            sys.exit()

    def __init__(self, fname, chan, **kwargs):
        self._verify(fname)
        self.fname=fname
        self.channel=chan
        self.streamid=kwargs.get('streamid',0)
    def _add_id3(self, f):
        pass
    def _write_block(self, f, data):
        pass
    def write(self):
        with open(self.fname, 'wb') as f:
            self._add_id3(f)
            for chunk in self.channel.chunks:
                index = Index(chunk)
                data = Data(chunk.rstrip(".idx"))
                while True:
                    try:
                        blk = index.next_block(self.streamid)
                        if blk.offset < data.size:
                            self._write_block(f, data.frame(blk))
                    except EOFError:
                        break
    def _verify(self, path):
        if os.path.exists(path):
            while True:
                rc = input(path + " exists. Overwrite [y|n]?")
                if rc == 'y':
                    os.remove(path)
                    break
                elif rc == 'n':
                    raise IOError(path)

class AacDump(Dump):
    def __init__(self, fname, chan, **kwargs):
        super().__init__(fname, chan, **kwargs)
        self.channelid=kwargs.get('channelid','')
        self.config=kwargs.get('config', 0)
    def _write_block(self, f, data):
        f.write(AdtsHeader(config=self.config).encode(len(data)))
        f.write(data)
    def _add_id3(self, f):
        tag = Tag()
        tag.add_frame(Frame(id='TPUB',
                            content='IStream'))
        tag.add_frame(Frame(id='TIT2',
                            content=self.channelid))
        f.write(tag.encode())

class AnnexBDump(Dump):
    def __init__(self, fname, chan, **kwargs):
        super().__init__(fname, chan, **kwargs)
        self.startcode=b'\x00\x00\x00\x01'
    def _write_block(self, f, data):
        f.write(self.startcode)
        f.write(data)
