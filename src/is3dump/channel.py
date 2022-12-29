"""Module describes IStream3 data channel"""
import os
import json
import struct


class Channel:
    """IStream3 channel"""
    @staticmethod
    def search_in_meta(metadata, searched_key):
        """recursive search in json by key"""
        result = ''
        if isinstance(metadata, type({})):
            for key in metadata:
                if key == searched_key:
                    return metadata[key]
                result = Channel.search_in_meta(metadata[key], searched_key)
                if len(result):
                    return result
        return result

    def __init__(self, path, stream_id=0):
        if os.path.exists(path) is False:
            raise IOError(path)

        self.chunks = []
        self.metadata = None
        for name in os.listdir(path):
            if name.endswith('.data.idx'):
                self.chunks.append(os.path.join(path, name))
            elif name.startswith('stream.'+str(stream_id)+'.'):
                with open(os.path.join(path, name)) as stream_file:
                    self.metadata = json.load(stream_file)
        self.chunks.sort()

    def search(self, key):
        """search in IStream3 channel json metadata by key"""
        return Channel.search_in_meta(self.metadata, key)


class Block:
    """IStream3 index entry"""
    def __init__(self, fd) -> None:
        self._block = fd.read(77)
        if len(self._block) != 77:
            raise EOFError()
        self.entry_size,\
            self.block_type,\
            self.stream_type,\
            self.stream_id,\
            self.flags,\
            self.duration,\
            self.timestamp,\
            self.ts_rel,\
            self.dts_rel,\
            self.block_size,\
            self.offset,\
            self.index,\
            self.block_id,\
            self.mark = struct.unpack('=BBBQQQQIIQQQQH', self._block)
        if self.mark != 0xbabe:
            raise EOFError

    def __repr__(self):
        return f'{self.__class__.__name__}(block_type={self.block_type})'

    def __str__(self):
        return f'{self.index}\t{self.block_id}\t{self.block_type}\t{self.stream_id}\t{self.stream_type}\t' \
               f'{self.duration}\t{self.flags}\t{self.block_size}\t{self.timestamp}\t{self.ts_rel}'

    @property
    def relative_timestamp(self):
        """returns block relative timestamp in data file"""
        return self.ts_rel

    def __len__(self):
        return self.block_size


class IndexIterator:
    """IStream3 index file iterator"""
    _file = None
    _end = 0

    def __next__(self):
        try:
            if self._file is not None:
                block = Block(self._file)
                if not self._end or block.timestamp <= self._end:
                    return block
            raise StopIteration
        except EOFError:
            raise StopIteration from None

    def filename(self, name):
        """Sets IStream3 index filename"""
        self._file = open(name, 'rb')

    filename = property(None, filename)

    def end(self, stop):
        """Sets IStream3 index timestamp to dump till"""
        self._end = stop

    end = property(None, end)


class Index:
    """IStream3 index file"""
    def __init__(self, path, last_timestamp):
        self._path = path
        self._last_timestamp = last_timestamp

    @property
    def path(self):
        """returns IStream3 index file path"""
        return self._path

    def __iter__(self):
        index_iterator = IndexIterator()
        index_iterator.filename = self._path
        index_iterator.end = self._last_timestamp
        return index_iterator


class Data:
    """IStream3 data file"""
    def __init__(self, path):
        self._size = os.path.getsize(path)
        self._file_desc = open(path, 'rb')

    def __len__(self):
        return self._size

    def frame(self, block) -> bytes:
        """Returns data frame by index block offset and index block size"""
        self._file_desc.seek(block.offset-len(block), 0)
        return self._file_desc.read(len(block))
