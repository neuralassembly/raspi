# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import numpy as np
from scipy import stats

version = cv2.__version__.split(".")
CVversion = int(version[0])

# 手の認識用パラメータ（HチャンネルとSチャンネルとを二値化するための条件）
hmin = 0
hmax = 30 # 15-40程度にセット
smin = 50

# グー、チョキ、パーのファイルの個数を格納する変数
gu_file_count = 0
choki_file_count = 0
pa_file_count = 0

# 二値化された画像を保存するための関数（自分の手の画像で学習したい方のみ用いる）
def save_hand(mode, img):
    global gu_file_count
    global choki_file_count
    global pa_file_count

    if mode == 'g':
        filename = 'img_gu{0:03d}.png'.format(gu_file_count)
        print('saving {0}'.format(filename))
        cv2.imwrite(filename, img)
        gu_file_count += 1
    elif mode == 'c':
        filename = 'img_choki{0:03d}.png'.format(choki_file_count)
        print('saving {0}'.format(filename))
        cv2.imwrite(filename, img)
        choki_file_count += 1
    elif mode == 'p':
        filename = 'img_pa{0:03d}.png'.format(pa_file_count)
        print('saving {0}'.format(filename))
        cv2.imwrite(filename, img)
        pa_file_count += 1

with picamera.PiCamera() as camera:
    with picamera.array.PiRGBArray(camera) as stream:
        # カメラの解像度を320x240にセット
        camera.resolution = (320, 240)
        # カメラのフレームレートを15fpsにセット
        camera.framerate = 15
        # ホワイトバランスをfluorescent(蛍光灯)モードにセット
        camera.awb_mode = 'fluorescent'

        while True:
            # stream.arrayにBGRの順で映像データを格納
            camera.capture(stream, 'bgr', use_video_port=True)

            # 映像データをHSV形式に変換
            hsv = cv2.cvtColor(stream.array, cv2.COLOR_BGR2HSV)
            # HSV形式からHチャンネルとSチャンネルの画像を得る
            hsv_channels = cv2.split(hsv)
            h_channel = hsv_channels[0]
            s_channel = hsv_channels[1]

            # Hチャンネルを平滑化
            h_binary = cv2.GaussianBlur(h_channel, (5,5), 0)

            # Hチャンネルの二値化画像を作成
            # hmin～hmaxの範囲を255（白）に、それ以外を0（黒）に
            ret,h_binary = cv2.threshold(h_binary, hmax, 255, cv2.THRESH_TOZERO_INV)
            ret,h_binary = cv2.threshold(h_binary, hmin, 255, cv2.THRESH_BINARY)
            # Sチャンネルの二値化画像を作成
            # smin～255の範囲を255（白）に、それ以外を0に（黒）に
            ret,s_binary = cv2.threshold(s_channel, smin, 255, cv2.THRESH_BINARY)

            # HチャンネルとSチャンネルの二値化画像のANDをとる
            # HチャンネルとSチャンネルの両方で255（白）の領域のみ白となる
            hs_and = h_binary & s_binary

            # 以下、最も広い白領域のみを残すための計算
            # まず、白領域の塊（クラスター）にラベルを振る
            if CVversion == 2: 
                img_dist, img_label = cv2.distanceTransformWithLabels(255-hs_and, cv2.cv.CV_DIST_L2, 5)
            else:
                img_dist, img_label = cv2.distanceTransformWithLabels(255-hs_and, cv2.DIST_L2, 5)
            img_label = np.uint8(img_label) & hs_and
            # ラベル0は黒領域なので除外
            img_label_not_zero = img_label[img_label != 0]
            # 最も多く現れたラベルが最も広い白領域のラベル
            if len(img_label_not_zero) != 0:
                m = stats.mode(img_label_not_zero)[0]
            else:
                m = 0
            # 最も広い白領域のみを残す
            hand = np.uint8(img_label == m)*255

            # 表示して動作チェックするため h_channel, s_channel, h_binary, s_binary を結合
            hs = np.concatenate((h_channel, h_binary), axis=0)
            hs_bin = np.concatenate((s_channel, s_binary), axis=0)
            hs_final = np.concatenate((hs_and, hand), axis=0)
            hs_all = np.concatenate((hs, hs_bin, hs_final), axis=1)

            # 得られた二値化画像を画面に表示
            cv2.imshow('hand', hand)
            # 動作チェック用の画像を画面に表示
            #cv2.imshow('HS', hs_all)
            #cv2.imshow('frame', stream.array)

            # 'q'を入力でアプリケーション終了
            # 'g', 'c', 'p'のときは画像保存
            key = cv2.waitKey(1) 
            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord('g'):
                save_hand('g', hand)
            elif key & 0xFF == ord('c'):
                save_hand('c', hand)
            elif key & 0xFF == ord('p'):
                save_hand('p', hand)

            # streamをリセット
            stream.seek(0)
            stream.truncate()

        cv2.destroyAllWindows()
