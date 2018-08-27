# -*- coding: utf-8 -*-
import keras
from keras import backend as K
import picamera
import picamera.array
import cv2
import numpy as np
from scipy import stats
import sys

version = cv2.__version__.split(".")
CVversion = int(version[0])

# 手の二値化画像のサイズ 縦(row)と横(col)
img_rows, img_cols = 12, 16

# 学習に用いる縮小画像のサイズ
sw = img_cols
sh = img_rows

# 手の認識用パラメータ（HチャンネルとSチャンネルとを二値化するための条件）
hmin = 0
hmax = 30 # 15-40程度にセット
smin = 50

janken_class =  ['グー', 'チョキ', 'パー']

# 学習済ファイルの確認
if len(sys.argv)==1:
    print('使用法: python ml-10-08-hand-cnn-load.py 学習済ファイル名.h5')
    sys.exit()
savefile = sys.argv[1]

# 学習済ファイルを読み込んでmodelを作成
model = keras.models.load_model(savefile)

def getImageVector(img):
    # 白い領域(ピクセル値が0でない領域)の座標を集める
    nonzero = cv2.findNonZero(img)
    # その領域を囲う四角形の座標と大きさを取得
    xx, yy, ww, hh = cv2.boundingRect(nonzero)
    # 白い領域を含む最小の矩形領域を取得
    img_nonzero = img[yy:yy+hh, xx:xx+ww]
    # 白い領域を(sw, sh)サイズに縮小するための準備
    img_small = np.zeros((sh, sw), dtype=np.uint8)
    # 画像のアスペクト比を保ったまま、白い領域を縮小してimg_smallにコピーする
    if 4*hh < ww*3 and hh > 0:
        htmp = int(sw*hh/ww)
        if htmp>0:
            img_small_tmp = cv2.resize(img_nonzero, (sw, htmp), interpolation=cv2.INTER_LINEAR)
            img_small[int((sh-htmp)/2):int((sh-htmp)/2)+htmp, 0:sw] = img_small_tmp
    elif 4*hh >= ww*3 and ww > 0:
        wtmp = int(sh*ww/hh)
        if wtmp>0:
            img_small_tmp = cv2.resize(img_nonzero, (wtmp, sh), interpolation=cv2.INTER_LINEAR)
            img_small[0:sh, int((sw-wtmp)/2):int((sw-wtmp)/2)+wtmp] = img_small_tmp
    # 0...1の範囲にスケーリングしてからリターンする
    return np.array([img_small.ravel()/255.])

print('認識を開始します')

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

            # 最大の白領域からkerasに入力するためのベクトルを取得
            hand_vector = getImageVector(hand)
            X = np.array(hand_vector)
            if K.image_data_format() == 'channels_first':
                X = X.reshape(X.shape[0], 1, img_rows, img_cols)
                input_shape = (1, img_rows, img_cols)
            else:
                X = X.reshape(X.shape[0], img_rows, img_cols, 1)
                input_shape = (img_rows, img_cols, 1)

            # 学習済の畳み込みニューラルネットワークから分類結果を取得
            result = model.predict_classes(X, verbose=0)
            # 分類結果を表示
            print(janken_class[result[0]])

            # 得られた二値化画像を画面に表示
            cv2.imshow('hand', hand)

            # 'q'を入力でアプリケーション終了
            key = cv2.waitKey(1) 
            if key & 0xFF == ord('q'):
                break

            # streamをリセット
            stream.seek(0)
            stream.truncate()

        cv2.destroyAllWindows()
