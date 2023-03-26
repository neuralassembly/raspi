# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2
import numpy as np
from scipy import stats
from sklearn.linear_model import Perceptron
from tensorflow import keras
from tensorflow.keras import backend as K
import sys
from PIL import Image, ImageTk
import threading
import time
import subprocess
try:
    import Tkinter as tk
except ImportError: # for Python 3
    import tkinter as tk

version = cv2.__version__.split(".")
CVversion = int(version[0])

# 手の認識用パラメータ（HチャンネルとSチャンネルとを二値化するための条件）
hmin = 0
hmax = 30  # 15-40程度にセット
smin = 50

# 手の二値化画像のサイズ 縦(row)と横(col)
img_rows, img_cols = 12, 16

# 学習に用いる縮小画像のサイズ
sw = img_cols
sh = img_rows

# じゃんけんの手のベクトル形式を格納した配列。入力データとして用いる
# グー [1, 0, 0], チョキ [0, 1, 0], パー [0, 0, 1]
janken_array = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

# グー, チョキ, パーの名称を格納した配列
janken_class =  ['グー', 'チョキ', 'パー']

# 過去何回分の手を覚えているか
n = 3

# じゃんけんの過去の手の初期化
# 人間の手とコンピュータの手をそれぞれn回分。さらに1回分につき3個の数字が必要
Jprev = np.zeros(3*n*2) 

# 過去の手（ベクトル形式）をランダムに初期化
for i in range(2*n):
    j = np.random.randint(0, 3)
    Jprev[3*i:3*i+3] = janken_array[j]

# 現在の手（0～2の整数）をランダムに初期化
j = np.random.randint(0, 3)

# 過去の手（入力データ）をscikit_learn用の配列に変換
Jprev_set = np.array([Jprev])
# 現在の手（ターゲット）をscikit_learn用の配列に変換
jnow_set = np.array([j])

# 三層ニューラルネットワークを定義
#clf_janken = MLPClassifier(hidden_layer_sizes=(200, ), random_state=None)
# 単純パーセプトロンを定義
clf_janken = Perceptron(random_state=None)
# ランダムな入力でオンライン学習を1回行う。
# 初回の学習では、あり得るターゲット(0, 1, 2)を分類器に知らせる必要がある
clf_janken.partial_fit(Jprev_set, jnow_set, classes=[0, 1, 2])

# 勝敗の回数を初期化
win = 0
draw = 0
lose = 0

# 状態保存用のフラグ
appliStop = False
jankenLoop = False
recognizedHand = 0
jankenFirst = False

# 学習済ファイルの確認
if len(sys.argv)==2:
    savefile = sys.argv[1]
    try:
        model = keras.models.load_model(savefile)
    except IOError:
        print('学習済ファイル{0}を開けません'.format(savefile))
        sys.exit()
    except AttributeError:
        print('TensorFlow 2 で作成した学習済ファイルしか開けません')
        sys.exit()
else:
    print('使用法: python ml-10-10-janken-deep-shorten.py 学習済ファイル.h5')
    sys.exit()

# X:画像から計算したベクトル、y:教師データ
X = np.empty((0,sw*sh), float) 
y = np.array([], int)

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

# 手の認識をし続ける関数
def imageProcessing():
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
                # 最大の白領域のみを残す
                hand = np.uint8(img_label == m)*255

                # 最大の白領域からscikit-learnに入力するためのベクトルを取得
                hand_vector = getImageVector(hand)

                # 学習済のニューラルネットワークから結果を取得
                X = np.array(hand_vector)
                if K.image_data_format() == 'channels_first':
                    X = X.reshape(X.shape[0], 1, img_rows, img_cols)
                    input_shape = (1, img_rows, img_cols)
                else:
                    X = X.reshape(X.shape[0], img_rows, img_cols, 1)
                    input_shape = (img_rows, img_cols, 1)
                result = model.predict_classes(X, verbose=0)

                # 分類結果をrecognizedHandに格納
                global recognizedHand
                recognizedHand = result[0]

                # 手と判定されている領域を表示
                cv2.imshow('hand', hand)

                # waitを入れる
                key = cv2.waitKey(1) 

                if appliStop == True:
                    break

                # streamをリセット
                stream.seek(0)
                stream.truncate()

            cv2.destroyAllWindows()
            app.jankenStop()
            app.quit()

class Application(tk.Frame):
    # 初期化用関数
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.w = 200
        self.h = 200
        self.pack()
        self.create_widgets()
        root.protocol('WM_DELETE_WINDOW', self.close_window)
        self.recogthread = threading.Thread(target=imageProcessing)
        self.recogthread.start()

    # アプリ終了時に呼ばれる関数
    def close_window(self):
        global jankenLoop
        global appliStop 
        jankenLoop = False
        appliStop = True

    # GUI部品の初期化
    def create_widgets(self):
        w = self.w
        h = self.h

        # コンピュータの手を表示する領域を初期化
        self.comp_canvas = tk.Canvas(self, width=w, height=h, bg='white')
        self.comp_blank_img = tk.PhotoImage(width=w, height=h)
        self.comp_canvas.create_image((w/2,h/2), image=self.comp_blank_img, state='normal')
        self.comp_canvas.image = self.comp_blank_img
        self.comp_canvas.grid(row=0, column=0)

        # コンピュータの手の画像の読み込み
        self.comp_gu_img = ImageTk.PhotoImage(image=Image.open('ml-images/comp_gu.png'))
        self.comp_choki_img = ImageTk.PhotoImage(image=Image.open('ml-images/comp_choki.png'))
        self.comp_pa_img = ImageTk.PhotoImage(image=Image.open('ml-images/comp_pa.png'))

        # 人間の手を表示する領域を初期化 
        self.human_canvas = tk.Canvas(self, width=w, height=h, bg='white')
        self.human_blank_img = tk.PhotoImage(width=w, height=h)
        self.human_canvas.create_image((w/2,h/2), image=self.human_blank_img, state='normal')
        self.human_canvas.image = self.human_blank_img
        self.human_canvas.grid(row=0, column=1)

        # 人間の手の画像の読み込み
        self.human_gu_img = ImageTk.PhotoImage(image=Image.open('ml-images/human_gu.png'))
        self.human_choki_img = ImageTk.PhotoImage(image=Image.open('ml-images/human_choki.png'))
        self.human_pa_img = ImageTk.PhotoImage(image=Image.open('ml-images/human_pa.png'))

        # メッセージ表示領域の初期化
        self.message_canvas = tk.Canvas(self, width=2*w, height=30, bg='white')
        self.message_canvas.grid(row=1, column=0, columnspan=2)

        # 結果表示領域の初期化
        self.result_canvas = tk.Canvas(self, width=2*w, height=30, bg='white')
        self.result_canvas.grid(row=2, column=0, columnspan=2)

        # じゃんけん開始ボタンの初期化
        self.janken_btn = tk.Button(self, text='じゃんけん開始', command=self.janken_start, relief='raised')
        self.janken_btn.grid(row=3, column=0)

        # クリアボタンの初期化
        self.reset_btn = tk.Button(self, text='集計のクリア', command=self.clear)
        self.reset_btn.grid(row=3, column=1)

    # クリアボタンが押されたときに呼ばれる関数
    def clear(self):
        global draw, lose, win
        draw = 0
        lose = 0
        win = 0
        self.message_canvas.delete('all')
        result_text = 'あなたの勝ち: {0:d}, 負け: {1:d}, あいこ: {2:d} '.format(win, lose, draw)
        self.result_canvas.delete('all')
        self.result_canvas.create_text(200, 15, text=result_text)

    # じゃんけんが動作中かチェックするための関数
    def jankenAlive(self):
        try:
            self.jankenthread.is_alive()
        except AttributeError:
            return False

    # じゃんけんを停止するための関数
    def jankenStop(self):
        try:
            self.jankenthread.join()
        except AttributeError:
            pass

    # じゃんけん開始ボタンが押されたときに呼ばれる関数
    def janken_start(self):
        global jankenLoop
        global jankenFirst
        if jankenLoop == False:
            jankenLoop = True
            jankenFirst = True
            if not self.jankenAlive():
                self.jankenthread = threading.Thread(target=self.janken_loop)
                self.jankenthread.start()
            self.janken_btn.config(relief='sunken')
            self.reset_btn.config(state='disabled')
        else:
            jankenLoop = False
            self.janken_btn.config(relief='raised')
            self.reset_btn.config(state='normal')

    # じゃんけんのループ
    def janken_loop(self):
        w = self.w
        h = self.h
        global jankenLoop
        global jankenFirst
        while jankenLoop == True:
            time.sleep(1)
            if jankenFirst == True:
                message_text = 'じゃんけん'
                self.message_canvas.delete('all')
                self.message_canvas.create_text(200, 15, text=message_text)
                args = ['mpg321', '-q', 'ml-sound/jankenpon.mp3']
                process = subprocess.Popen(args).wait()
                jankenFirst = False
            else:
                args = ['mpg321', '-q', 'ml-sound/pon.mp3']
                process = subprocess.Popen(args).wait()
            # メッセージ領域に「ぽん！」と表示
            message_text = 'ぽん！'
            self.message_canvas.delete('all')
            self.message_canvas.create_text(200, 15, text=message_text)

            # 人間の手を画像処理の結果から決定
            j = recognizedHand
            global Jprev
            # 過去のじゃんけんの手（ベクトル形式）をscikit_learn形式に
            Jprev_set = np.array([Jprev])
            # 現在のじゃんけんの手（0～2の整数）をscikit_learn形式に
            jnow_set = np.array([j])

            # コンピュータが、過去の手から人間の現在の手を予測
            jpredict = clf_janken.predict(Jprev_set)

            # 人間の手
            your_choice = j
            # 予測を元にコンピュータが決めた手
            # 予測がグーならパー、予測がチョキならグー、予測がパーならチョキ
            comp_choice = (jpredict[0] + 2)%3

            if comp_choice == 0:
                # コンピュータのグー画像表示
                self.comp_canvas.create_image((w/2,h/2), image=self.comp_gu_img, state='normal')
                self.comp_canvas.image = self.comp_gu_img
            elif comp_choice == 1:
                # コンピュータのチョキ画像表示
                self.comp_canvas.create_image((w/2,h/2), image=self.comp_choki_img, state='normal')
                self.comp_canvas.image = self.comp_choki_img
            else:
                # コンピュータのパー画像表示
                self.comp_canvas.create_image((w/2,h/2), image=self.comp_pa_img, state='normal')
                self.comp_canvas.image = self.comp_pa_img

            if your_choice == 0:
                # 人間のグー画像表示
                self.human_canvas.create_image((w/2,h/2), image=self.human_gu_img, state='normal')
                self.human_canvas.image = self.human_gu_img
            elif your_choice == 1:
                # 人間のチョキ画像表示
                self.human_canvas.create_image((w/2,h/2), image=self.human_choki_img, state='normal')
                self.human_canvas.image = self.human_choki_img
            else:
                # 人間のパー画像表示
                self.human_canvas.create_image((w/2,h/2), image=self.human_pa_img, state='normal')
                self.human_canvas.image = self.human_pa_img

            # 勝敗結果を更新 
            global draw, lose, win
            if your_choice == comp_choice:
                draw += 1
            elif your_choice == (comp_choice+1)%3:
                lose += 1
            else:
                win += 1

            # 勝敗結果を表示
            result_text = 'あなたの勝ち: {0}, 負け: {1}, あいこ: {2} '.format(win, lose, draw)
            self.result_canvas.delete('all')
            self.result_canvas.create_text(200, 15, text=result_text)
           
            # 過去の手（入力データ）と現在の手（ターゲット）とでオンライン学習 
            clf_janken.partial_fit(Jprev_set, jnow_set)

            # 過去の手の末尾に現在のコンピュータの手を追加
            Jprev = np.append(Jprev[3:], janken_array[comp_choice])
            # 過去の手の末尾に現在の人間の手を追加
            Jprev = np.append(Jprev[3:], janken_array[your_choice])

root = tk.Tk()
app = Application(master=root)
app.master.title('ディープじゃんけん(音声短縮版)')
app.mainloop()
