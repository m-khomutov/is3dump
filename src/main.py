"""Starts stream dumping from IStream3 channel"""
import sys
import istream3dumper.dump

if __name__ == '__main__':
    dumper = istream3dumper.dump.Dump.make(sys.argv[1:])
    if dumper is not None:
        dumper.write()
