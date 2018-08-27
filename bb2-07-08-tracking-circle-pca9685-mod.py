# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import math
from time import sleep
import smbus
import math

version = cv2.__version__.split(".")
CVversion = int(version[0])

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

def getPCA9685Duty(id, val):
    val_min = 0
    val_max = 4095
    servo_min = 143 # 50Hzで0.7ms
    servo_max = 410 # 50Hzで2.0ms  (中心は276)
    if id==1 :
        servo_min = 193 # 50Hzで0.95ms
        servo_max = 360 # 50Hzで1.8ms
    duty = (servo_min-servo_max)*(val-val_min)/(val_max-val_min) + servo_max
    # 一般的なサーボモーターはこちらを有効に
    #duty = (servo_max-servo_min)*(val-val_min)/(val_max-val_min) + servo_min
    if duty > servo_max:
        duty = servo_max
    if duty < servo_min:
        duty = servo_min
    return int(duty)

bus = smbus.SMBus(1)
address_pca9685 = 0x40

resetPCA9685()
setPCA9685Freq(50)

prev_x = 160
prev_y = 120
prev_input_x = 2048
prev_input_y = 2048

with picamera.PiCamera() as camera:
    with picamera.array.PiRGBArray(camera) as stream:
        camera.resolution = (320, 240)

        while True:
            # stream.arrayにBGRの順で映像データを格納
            camera.capture(stream, 'bgr', use_video_port=True)
            # 映像データをグレースケール画像grayに変換
            gray = cv2.cvtColor(stream.array, cv2.COLOR_BGR2GRAY)
            # ガウシアンぼかしを適用して、認識精度を上げる
            blur = cv2.GaussianBlur(gray, (9,9), 0)
            # ハフ変換を適用し、映像内の円を探す
            if CVversion == 2:
                circles = cv2.HoughCircles(blur, cv2.cv.CV_HOUGH_GRADIENT,
                      dp=1, minDist=50, param1=120, param2=40,
                      minRadius=5, maxRadius=100)
            else:
                circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT,
                      dp=1, minDist=50, param1=120, param2=40,
                      minRadius=5, maxRadius=100)

            if circles is not None:
                # 複数見つかった円のうち、以前の円の位置に最も近いものを探す
                mindist = 320+240
                minindx = 0
                indx = 0
                for c in circles[0]:
                    dist = math.fabs(c[0]-prev_x) + math.fabs(c[1]-prev_y)
                    if dist < mindist:
                        mindist = dist
                        minindx = indx
                    indx += 1

                # 現在の円の位置
                circle_x = circles[0][minindx][0]
                circle_y = circles[0][minindx][1]

                # 現在の円の位置に赤い円を元の映像(system.array)上に描画
                cv2.circle(stream.array, (circle_x, circle_y),
                      circles[0][minindx][2], (0,0,255), 2)

                dx = circle_x-160  # 左右中央からのずれ
                dy = circle_y-120  # 上下中央からのずれ

                # サーボモーターを回転させる量を決める定数
                ratio_x =  3
                ratio_y = -3

                duty0 = getPCA9685Duty(0, ratio_x*dx + prev_input_x)
                setPCA9685Duty(0, 0, duty0)

                duty1 = getPCA9685Duty(1, ratio_y*dy + prev_input_y)
                setPCA9685Duty(1, 0, duty1)

                # サーボモーターに対する入力値を更新
                prev_input_x = ratio_x*dx + prev_input_x
                if prev_input_x > 4095:
                    prev_input_x = 4095
                if prev_input_x < 0:
                    prev_input_x = 0
                prev_input_y = ratio_y*dy + prev_input_y
                if prev_input_y > 4095:
                    prev_input_y = 4095
                if prev_input_y < 0:
                    prev_input_y = 0

                # 以前の円の位置を更新
                prev_x = circle_x
                prev_y = circle_y

            # system.arrayをウインドウに表示
            cv2.imshow('frame', stream.array)

            # "q"を入力でアプリケーション終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # streamをリセット
            stream.seek(0)
            stream.truncate()

        cv2.destroyAllWindows()
