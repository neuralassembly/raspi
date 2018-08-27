# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import math
import wiringpi2 as wiringpi

version = cv2.__version__.split(".")
CVversion = int(version[0])

def getServoDutyHw(id, val):
    val_min = 0
    val_max = 4095
    # デューティ比0%を0、100%を1024として数値を入力
    servo_min = 36   # 50Hz(周期20ms)、デューティ比3.5%: 3.5*1024/100=約36
    servo_max = 102  # 50Hz(周期20ms)、デューティ比10%: 10*1024/100=約102
    if id==1:
        servo_min = 53
        servo_max = 85
    duty = int((servo_min-servo_max)*(val-val_min)/(val_max-val_min) + servo_max)
    # 一般的なサーボモーターはこちらを有効に
    #duty = int((servo_max-servo_min)*(val-val_min)/(val_max-val_min) + servo_min)
    if duty > servo_max:
        duty = servo_max
    if duty < servo_min:
        duty = servo_min
    return duty

PWM0 = 18
PWM1 = 19

# wiringPiによるハードウェアPWM
wiringpi.wiringPiSetupGpio() # GPIO名で番号を指定する
wiringpi.pinMode(PWM0, wiringpi.GPIO.PWM_OUTPUT) # 左右方向のPWM出力を指定
wiringpi.pinMode(PWM1, wiringpi.GPIO.PWM_OUTPUT) # 上下方向のPWM出力を指定
wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS) # 周波数を固定するための設定
wiringpi.pwmSetClock(375) # 50 Hz。18750/(周波数) の計算値に近い整数
# PWMのピン番号とデフォルトのパルス幅をデューティ100%を1024として指定。
# ここでは6.75%に対応する69を指定
wiringpi.pwmWrite(PWM0, 69)
wiringpi.pwmWrite(PWM1, 69)

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

                duty0 = getServoDutyHw(0, ratio_x*dx + prev_input_x)
                wiringpi.pwmWrite(PWM0, duty0)

                duty1 = getServoDutyHw(1, ratio_y*dy + prev_input_y)
                wiringpi.pwmWrite(PWM1, duty1)

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
