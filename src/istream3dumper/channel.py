"""Module describes IStream3 data channel"""
import os
import json


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

    def __init__(self, path, stream_id):
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
    def __init__(self, fd):
        self._block = fd.read(77)
        if len(self._block) != 77:
            raise EOFError()
        self._stream_id = int.from_bytes(self._block[3:11], 'little')
        self._ts_rel = int.from_bytes(self._block[35:39], 'little')
        self._size = int.from_bytes(self._block[43:51], 'little')
        self._offset = int.from_bytes(self._block[51:59], 'little')

    @property
    def offset(self):
        """returns block offset in data file"""
        return self._offset

    @property
    def stream_id(self):
        """returns block stream id in data file"""
        return self._stream_id

    @property
    def relative_timestamp(self):
        """returns block relative timestamp in data file"""
        return self._ts_rel

    def __len__(self):
        return self._size

    def __repr__(self):
        return "size="+str(self._block[0]) + \
               " index="+str(int.from_bytes(self._block[59:67], 'little')) + \
               " block id="+str(int.from_bytes(self._block[67:75], 'little')) + \
               " block type="+str(self._block[1]) + \
               " stream id="+str(self._stream_id) + \
               " stream type="+str(self._block[2]) + \
               " duration="+str(int.from_bytes(self._block[19:27], 'little')) + \
               " flags="+hex(int.from_bytes(self._block[11:19], 'little')) + \
               " block size="+str(self._size) + \
               " timestamp="+str(int.from_bytes(self._block[27:35], 'little')) + \
               " ts="+str(self._ts_rel) + \
               " dts="+str(int.from_bytes(self._block[39:43], 'little')) + \
               " offset="+str(self._offset) + \
               " mark="+hex(int.from_bytes(self._block[75:77], 'little'))


class IndexIterator:
    """IStream3 index file iterator"""
    _file = None

    def filename(self, name):
        """Sets IStream3 index filename"""
        self._file = open(name, 'rb')

    filename = property(None, filename)

    def __next__(self):
        try:
            if self._file is not None:
                return Block(self._file)
            raise StopIteration
        except EOFError:
            raise StopIteration from None


class Index:
    """IStream3 index file"""
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        """returns IStream3 index file path"""
        return self._path

    def __iter__(self):
        index_iterator = IndexIterator()
        index_iterator.filename = self._path
        return index_iterator


class Data:
    """IStream3 data file"""
    def __init__(self, path):
        self._size = os.path.getsize(path)
        self._file_desc = open(path, 'rb')

    def __len__(self):
        return self._size

    def frame(self, block):
        """Returns data frame by index block offset and index block size"""
        self._file_desc.seek(block.offset-len(block), 0)
        return self._file_desc.read(len(block))
