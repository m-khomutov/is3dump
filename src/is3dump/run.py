import getopt
import sys
from .dump import Dump
from .stream import make_stream_files


def show_params():
    """Shows command line parameters"""
    print("params:\n\t-c(--channel) path to channel directory (req.)\n\t"
          "-i(--id) stream id (def. 0)\n\t"
          "-d(--dump) path to dumpfile(def. ./channel_id)\n\t"
          "-r(--range) dumping range (from, to) (def. (begin, end))\n\t"
          "-o(--override) override existing file (def. exit without overriding)\n\t"
          "-v(--verb) be verbose - show index blocks\n\t"
          "-s(--stream) store stream files\n\t"
          "-h(--help) this help")
    sys.exit()


def get_params(argv):
    """Returns command line parameters"""
    channel_path = ''
    stream_id = 0
    dump_path = ''
    dump_range = ()
    is_verbose = False
    override = False
    store_streams = False
    opts = ()
    try:
        opts, remainder = getopt.getopt(argv,
                                        "c:i:d:r:ovsh",
                                        ["channel=", "id=", "dump=", "range=",
                                         "override", "verb", "stream", "help"])
        if len(remainder):
            raise getopt.GetoptError('invalid options: ' + ' '.join(remainder))
    except getopt.GetoptError as opt_error:
        print(opt_error)
        show_params()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_params()
        elif opt in ('-c', '--channel'):
            channel_path = arg
        elif opt in ('-i', '--id'):
            stream_id = int(arg)
        elif opt in ('-d', '--dump'):
            dump_path = arg
        elif opt in ('-r', '--range'):
            dump_range = tuple(int(k) if len(k) else 0 for k in arg.split(','))
        elif opt in ('-o', '--override'):
            override = True
        elif opt in ('-v', '--verb'):
            is_verbose = True
        elif opt in ('-s', '--stream'):
            store_streams = True
    if len(channel_path) == 0:
        show_params()
    return channel_path, stream_id, dump_path, dump_range, override, is_verbose, store_streams


def run():
    params = get_params(sys.argv[1:])
    if params[-1]:
        make_stream_files(params[0])
    else:
        Dump.make(*params).write()
