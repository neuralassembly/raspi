#!/bin/bash

HTSVOICE=/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice
#HTSVOICE=/usr/share/hts-voice/mei/mei_happy.htsvoice
#HTSVOICE=/usr/share/hts-voice/mei/mei_angry.htsvoice
#HTSVOICE=/usr/share/hts-voice/mei/mei_bashful.htsvoice
#HTSVOICE=/usr/share/hts-voice/mei/mei_normal.htsvoice
#HTSVOICE=/usr/share/hts-voice/mei/mei_sad.htsvoice

DICDIR=/var/lib/mecab/dic/open-jtalk/naist-jdic/
TMPVOICE=/tmp/voice.wav

echo "$1" | open_jtalk -x $DICDIR -m $HTSVOICE -ow $TMPVOICE 

# for the device on Raspberry Pi
aplay -q $TMPVOICE

# for USB sound card
#aplay -D plughw:1,0 -q $TMPVOICE

rm -f $TMPVOICE
