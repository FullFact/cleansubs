"""Split a stream of subtitles into sentences and print them to stdout.

The stream can be piped in like this:
`mosquitto_sub -h iot.eclipse.org -t "bbc/subtitles/bbc_news24/raw"
 | python3 sentence_stream.py`
"""

import sys
import cleansubs


def print_line(line):
    print(line + '\n')

sentencer = cleansubs.Sentencer(print_line)

for line in sys.stdin:
    sentencer.process(line)
