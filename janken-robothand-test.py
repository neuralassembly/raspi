# -*- coding: utf-8 -*-
from time import sleep
import smbus
import math
import sys

if len(sys.argv)<=1:
    print('python guchokipa.py [0,1,2]')
    sys.exit()

def resetPCA9685():
    bus.write_byte_data(address_pca9685, 0x00, 0x00)

def setPCA9685Freq(freq):
    freq = 0.9*freq # Arduinoのライブラリより
    prescaleval = 25000000.0    # 25MHz
    prescaleval /= 4096.0       # 12-bit
    prescaleval /= float(freq)
    prescaleval -= 1.0
    prescale = int(math.floor(prescaleval + 0.5))
    oldmode = bus.read_byte_data(address_pca9685, 0x00)
    newmode = (oldmode & 0x7F) | 0x10             # スリープモード
    bus.write_byte_data(address_pca9685, 0x00, newmode) # スリープモードへ
    bus.write_byte_data(address_pca9685, 0xFE, prescale) # プリスケーラーをセット
    bus.write_byte_data(address_pca9685, 0x00, oldmode)
    sleep(0.005)
    bus.write_byte_data(address_pca9685, 0x00, oldmode | 0xa1)

def setPCA9685Duty(channel, on, off):
    channelpos = 0x6 + 4*channel
    try:
        bus.write_i2c_block_data(address_pca9685, channelpos, [on&0xFF, on>>8, off&0xFF, off>>8] )
    except IOError:
        pass

bus = smbus.SMBus(1)
address_pca9685 = 0x40

resetPCA9685()
setPCA9685Freq(50)

def guchokipa_servo(i):
    if i==0: #グーのとき
        # 順に、親指〜小指に対応するサーボの値。
        # 2番目の引数は常に0。範囲は143〜410程度で276がゼロ点。
        # 以下同様。
        setPCA9685Duty(0, 0, 350)
        sleep(0.01)
        setPCA9685Duty(1, 0, 220)
        sleep(0.01)
        setPCA9685Duty(2, 0, 240)
        sleep(0.01)
        setPCA9685Duty(3, 0, 220)
        sleep(0.01)
        setPCA9685Duty(4, 0, 350)
    elif i==1: #チョキのとき
        setPCA9685Duty(0, 0, 350)
        sleep(0.01)
        setPCA9685Duty(1, 0, 380)
        sleep(0.01)
        setPCA9685Duty(2, 0, 360)
        sleep(0.01)
        setPCA9685Duty(3, 0, 220)
        sleep(0.01)
        setPCA9685Duty(4, 0, 350)
    elif  i==2: #パーのとき
        setPCA9685Duty(0, 0, 190)
        sleep(0.01)
        setPCA9685Duty(1, 0, 380)
        sleep(0.01)
        setPCA9685Duty(2, 0, 360)
        sleep(0.01)
        setPCA9685Duty(3, 0, 360)
        sleep(0.01)
        setPCA9685Duty(4, 0, 210)

guchokipa_servo(int(sys.argv[1]))

