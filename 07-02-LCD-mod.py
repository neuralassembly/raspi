# -*- coding: utf-8 -*-
import smbus
import sys
from time import sleep

def setup_aqm0802a():
    trials = 5
    for i in range(trials):
        try:
            c_lower = (contrast & 0xf)
            c_upper = (contrast & 0x30)>>4
            bus.write_i2c_block_data(address_aqm0802a, register_setting, [0x38, 0x39, 0x14, 0x70|c_lower, 0x54|c_upper, 0x6c])
            sleep(0.2)
            bus.write_i2c_block_data(address_aqm0802a, register_setting, [0x38, 0x0d, 0x01])
            sleep(0.001)
            break
        except IOError:
            if i==trials-1:
                sys.exit()

def clear():
    global position
    global line
    position = 0
    line = 0
    bus.write_byte_data(address_aqm0802a, register_setting, 0x01)
    sleep(0.001)

def newline():
    global position
    global line
    if line == display_lines-1:
        clear()
    else:
        line += 1
        position = chars_per_line*line
        bus.write_byte_data(address_aqm0802a, register_setting, 0xc0)
        sleep(0.001)

def write_string(s):
    for c in list(s):
        write_char(ord(c))

def write_char(c):
    global position
    byte_data = check_writable(c)
    if position == display_chars:
        clear()
    elif position == chars_per_line*(line+1):
        newline()
    bus.write_byte_data(address_aqm0802a, register_display, byte_data)
    position += 1

def check_writable(c):
    if c >= 0x06 and c <= 0xff :
        return c
    else:
        return 0x20 # 空白文字

bus = smbus.SMBus(1)
address_aqm0802a = 0x3e
register_setting = 0x00
register_display = 0x40

contrast = 32 # 0から63のコントラスト。通常は32、文字が薄いときは40を推奨
chars_per_line = 8  # LCDの横方向の文字数
display_lines = 2   # LCDの行数

display_chars = chars_per_line*display_lines

position = 0
line = 0

setup_aqm0802a()

if len(sys.argv)==1:
    # アルファベットと記号は「''」でくくってそのまま表示可能
    write_string('Hello World')

    # カタカナや特殊記号は文字コードを一文字ずつ入力
    # 以下は「ラズベリー パイ」と表示する例
    #s = chr(0xd7)+chr(0xbd)+chr(0xde)+chr(0xcd)+chr(0xde)+chr(0xd8)+chr(0xb0)+' '+chr(0xca)+chr(0xdf)+chr(0xb2)
    #write_string(s)
else:
    write_string(sys.argv[1])

