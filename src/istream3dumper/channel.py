import os
import json

class Channel:
    @staticmethod
    def search_in_meta(v, k):
        rc=''
        if type(v) == type({}):
            for k1 in v:
                if k1 == k:
                    return v[k1]
                rc=Channel.search_in_meta(v[k1], k)
                if len(rc):
                    return rc
        return rc
    def __init__(self, path, streamid):
        if os.path.exists(path) == False:
            raise IOError(path)

        self.chunks=[]
        self.metadata=None
        for root, dir, files in os.walk(path):
            for f in files:
                if f.endswith('.data.idx'):
                    self.chunks.append(os.path.join(root, f))
                elif f.startswith('stream.'+str(streamid)+'.'):
                    with open(os.path.join(root,f)) as fd:
                        self.metadata=json.load(fd)

        self.chunks.sort()
    def search(self, key):
        return Channel.search_in_meta(self.metadata, key)

class Entry:
    def __init__(self, fd):
        b=fd.read( 77 )
        if len(b) != 77:
            raise EOFError()
        self.entrySize = b[0]
        self.blockType = b[1]
        self.streamType = b[2]
        self.streamId = int.from_bytes(b[3:11],'little')
        self.flags = int.from_bytes(b[11:19],'little')
        self.duration = int.from_bytes(b[19:27],'little')
        self.timestamp = int.from_bytes(b[27:35],'little')
        self.ts_rel = int.from_bytes(b[35:39],'little')
        self.dts_rel = int.from_bytes(b[39:43],'little')
        self.size = int.from_bytes(b[43:51],'little')
        self.offset = int.from_bytes(b[51:59],'little')
        self.index = int.from_bytes(b[59:67],'little')
        self.blockId = int.from_bytes(b[67:75],'little')
        self.mark = int.from_bytes(b[75:77],'little')
    def __str__(self):
        return "size="+str(self.entrySize)+\
               "\nindex="+str(self.index)+\
               "\nblock id="+str(self.blockId)+\
               "\nblock type="+str(self.blockType)+\
               "\nstream id="+str(self.streamId)+\
               "\nstream type="+str(self.streamType)+\
               "\nduration="+str(self.duration)+\
               "\nflags="+hex(self.flags)+\
               "\nblock size="+str(self.size)+\
               "\ntimestamp="+str(self.timestamp)+\
               "\nts="+str(self.ts_rel)+\
               "\ndts="+str(self.dts_rel)+\
               "\noffset="+str(self.offset)+\
               "\nmark="+hex(self.mark)

class Index:
    def __init__(self, path):
        self.indexfd=open(path, 'rb')
    def __del__(self):
        self.indexfd.close()
    def next_block(self, stream_id):
        while True:
            e=Entry(self.indexfd)
            if e.streamId == stream_id:
                return e
        raise EOFError

class Data:
    def __init__(self, path):
        self.size=os.path.getsize(path)
        self.indexfd = open(path, 'rb')
    def __del__(self):
        self.indexfd.close()
    def frame(self, index):
        self.indexfd.seek(index.offset-index.size,0)
        return self.indexfd.read(index.size)