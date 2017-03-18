# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import smbus
import sys
from time import sleep
import requests

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

def read_adt7410():
    word_data = bus.read_word_data(address_adt7410, register_adt7410)
    data = (word_data & 0xff00)>>8 | (word_data & 0xff)<<8
    data = data>>3 # 13ビットデータ
    if data & 0x1000 == 0:  # 温度が正または0の場合
        temperature = data*0.0625
    else: # 温度が負の場合、 絶対値を取ってからマイナスをかける
        temperature = ( (~data&0x1fff) + 1)*-0.0625
    return temperature

def my_callback(channel):
    if channel==24:
        global mode
        mode = (mode+1)%3
        try:
            displayWeather()
        except IOError:
            pass

try:
    unicode # python2
    def u(str): return str.decode('utf-8')
    pass
except: # python3
    def u(str): return str
    pass

# 最低気温と最高気温を「/」区切りの文字列に
def getLCDMinMax(temp):
    if temp['min'] != None:
        min = '{0}'.format(temp['min']['celsius'])
    else:
        min = '--'

    if temp['max'] != None:
        max = '{0}'.format(temp['max']['celsius'])
    else:
        max = '--'
    return min + '/' + max

# 天気をカタカナの文字列に
def getLCDWeather(weather):
    if weather.find(u('のち')) != -1:
        datas = weather.split(u('のち')) 
        return replaceWeather(datas[0])+chr(0x3e)+replaceWeather(datas[1]) # >
    elif weather.find(u('時々')) != -1:
        datas = weather.split(u('時々'))
        return replaceWeather(datas[0])+'/'+replaceWeather(datas[1])
    else:
        return replaceWeather(weather)

# 各天気をカタカナに
def replaceWeather(weather):
    if weather.find(u('晴')) != -1:
        return chr(0xca)+chr(0xda) # ハレ
    elif weather.find(u('曇')) != -1:
        return chr(0xb8)+chr(0xd3)+chr(0xd8) # クモリ
    elif weather.find(u('雨')) != -1:
        return chr(0xb1)+chr(0xd2) # アメ
    elif weather.find(u('雪')) != -1:
        return chr(0xd5)+chr(0xb7) # ユキ
    else:
        return '--'

# Webサービスより天気予報を取得
def getWeather():
    global minmax, weather, minmax2, weather2
    location = 130010  # 東京
    proxies = None
    # proxy環境下の方は下記を記述して有効に
    #proxies = {
    #    'http': 'プロキシサーバ名:ポート番号',
    #    'https': 'プロキシサーバ名:ポート番号'
    #}
    try:
        weather_json = requests.get(
            'http://weather.livedoor.com/forecast/webservice/json/v1?city={0}'.format(location), proxies=proxies, timeout=5
        ).json()
        print('インターネットから天気予報データを入手しました')
    except requests.exceptions.RequestException:
        print('ネットワークエラー')
        if second==0:
            sys.exit()
    for forecast in weather_json['forecasts']:
        if forecast['dateLabel'] == u('今日'):
            minmax = getLCDMinMax(forecast['temperature'])
            weather = getLCDWeather(forecast['telop'])
        if forecast['dateLabel'] == u('明日'):
            minmax2 = getLCDMinMax(forecast['temperature'])
            weather2 = getLCDWeather(forecast['telop'])

# 天気情報をLCDに表示
def displayWeather():
    clear()
    if temperature != 999:
        s = '{0:.1f}'.format(temperature) # 小数点以下1桁
    else:
        s = ''
    if mode==0:
        day = chr(0xb7)+chr(0xae)+chr(0xb3) # キョウ
        for i in range(chars_per_line-len(day)-len(s)):
            s = ' '+s
        write_string(day+s+weather)
    elif mode==1:
        day = chr(0xb7)+chr(0xae)+chr(0xb3) # キョウ
        for i in range(chars_per_line-len(day)-len(s)):
            s = ' '+s
        write_string(day+s+minmax)
    elif mode==2:
        day = chr(0xb1)+chr(0xbd) # アス
        s = minmax2
        for i in range(chars_per_line-len(day)-len(s)):
            s = ' '+s
        write_string(day+s+weather2)

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

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(24, GPIO.RISING, callback=my_callback, bouncetime=200)

address_adt7410 = 0x48
register_adt7410 = 0x00

mode = 0
temperature = 999
minmax = ''
weather = ''
minmax2 = ''
weather2 = ''

second = 0  # プログラム起動時から経過した秒数(目安)
hour = 0    # プログラム起動時から経過した時間(目安)
prevhour = -1  # 前回天気予報を問い合わせた時間

try:
    while True:
    
        if hour != prevhour: # 前回問い合わせより約1時間後
            getWeather()     # 天気予報取得
            prevhour = hour

        try:
            temperature = read_adt7410() # 温度取得
        except IOError:
            temperature = 999  # 温度取得失敗

        try:
            displayWeather()  # LCDに情報表示
        except IOError:
            print('I2C通信エラースキップ')

        second = second + 1 # 1秒進める 
        hour = int(second/3600)  # 秒を時間に変換(0,1,2,…のように整数のみ)

        sleep(1)

except KeyboardInterrupt:
    pass

GPIO.cleanup()
