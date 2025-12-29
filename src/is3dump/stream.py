import base64
import json
from .channel import Block, Index, Channel, Data


class AvcStream:
    def __init__(self):
        self._sprop_string: str = ''
        self._profile_level_id = ''
        self._sps, self._pps = '', ''

    def __str__(self):
        return json.dumps({'clock-rate': 90000,
                           'current-sprop-string': self._sprop_string,
                           'fixed-frame-rate': False,
                           'fps': 0.0000,
                           'height': 0,
                           'profile-level-id': self._profile_level_id,
                           'sprop-string-list': [self._sprop_string],
                           'stream_traits': {"encoding": "h264", "mediaType": "video"},
                           'width': 0},
                          separators=(',', ':'))

    def on_block(self, blk: Block, data: Data) -> None:
        if self._sprop_string:
            return
        if blk.stream_type == 1 and blk.block_type == 7:
            frame = data.frame(blk)
            self._profile_level_id = ''.join([f'{c:02X}' for c in frame[1:4]])
            self._sps = base64.b64encode(frame) + b','
        elif blk.stream_type == 1 and blk.block_type == 8:
            self._pps = base64.b64encode(data.frame(blk))
        if self._sps and self._pps:
            self._sprop_string = (self._sps + self._pps).decode('utf-8')

    def ready(self) -> bool:
        return len(self._sprop_string) > 0


class AacStream:
    def __init__(self):
        self._config: str = ''

    def on_block(self, blk: Block, data: Data) -> None:
        frame = data.frame(blk)
        self._config = '18856e500'

    def __str__(self):
        return json.dumps({"channel-config": 2,
                           "clock-rate": 16000,
                           "fmtp": "97 streamType=0;"
                                   "profile-level-id=1;"
                                   "config=118856e500;"
                                   "mode=AAC-hbr;"
                                   "SizeLength=13;"
                                   "IndexLength=3;"
                                   "IndexDeltaLength=3",
                           "freq": 16000,
                           "sample-frequency-index": 8,
                           "stream_traits": {"encoding": "aac", "mediaType": "audio"},
                           "stream_type": 3},
                          separators=(',', ':'))

    def ready(self) -> bool:
        return len(self._config) > 0


def make_stream_files(channel_path: str):
    channel: Channel = Channel(channel_path)
    avc_stream: AvcStream = AvcStream()
    aac_stream: AacStream = AacStream()
    for chunk in channel.chunks:
        data = Data(chunk.rstrip(".idx"))
        for blk in Index(chunk, 0):
            if blk.stream_type == 1:
                avc_stream.on_block(blk, data)
            elif blk.stream_type == 3:
                aac_stream.on_block(blk, data)
            if avc_stream.ready():
                with open('stream.0.1.json', 'w') as f:
                    f.write(str(avc_stream))
            if aac_stream.ready():
                with open('stream.2.3.json', 'w') as f:
                    f.write(str(aac_stream))
        break
