# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep
import spidev

# MCP3208からSPI通信で12ビットのデジタル値を取得。0から7の8チャンネル使用可
def readadc_spidev(adcnum):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    command1 = 0x6 | (adcnum & 0x4)>>2
    command2 = (adcnum & 0x3)<<6
    ret=spi.xfer2([command1,command2,0])
    adcout = (ret[1]&0xf)<<8 | ret[2]
    return adcout

GPIO.setmode(GPIO.BCM)
spi=spidev.SpiDev()
spi.open(0, 0) # bus0, CE0
spi.max_speed_hz = 1000000 # 1MHz

try:
    while True:
        inputVal0 = readadc_spidev(0)
        print(inputVal0)
        sleep(0.2)

except KeyboardInterrupt:
    pass

spi.close()
