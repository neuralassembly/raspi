# -*- coding: utf-8 -*-
import cv2
import sys
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.externals import joblib
import pylab as plt

# 学習に用いる縮小画像のサイズ
sw = 16
sh = 12

# 学習結果を保存するファイルの決定
if len(sys.argv)!=2:
    print('使用法: python ml-08-03-learn.py 保存ファイル名.pkl')
    sys.exit()
savefile = sys.argv[1]

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

# X:画像から計算したベクトル、y:教師データ
X = np.empty((0,sw*sh), float) 
y = np.array([], int)

# グー、チョキ、パー画像の読み込み
for hand_class in [0, 1, 2]: # 0:グー、1:チョキ、2:パー
    # 画像番号0から999まで対応
    for i in range(1000):
        if hand_class==0: #グー画像
            filename = 'ml-learn/img_gu{0:03d}.png'.format(i)
        elif hand_class==1: #チョキ画像
            filename = 'ml-learn/img_choki{0:03d}.png'.format(i)
        elif hand_class==2: #パー画像
            filename = 'ml-learn/img_pa{0:03d}.png'.format(i)

        img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        if img is None:
            break
        print('{0}を読み込んでいます'.format(filename))
        # 画像サイズ(lx, ly)と、回転中心座標(cx, cy)の取得
        ly, lx = img.shape[0:2]
        cx, cy = lx/2, ly/2
        # 学習データの格納
        for flip in [0, 1]: # 左右反転なし(0)とあり(1)
            if flip == 1:
                img = cv2.flip(img, 1)
            for angle in [-80, -60, -40, -20, 0, 20, 40, 60, 80]: #角度
                # 回転行列準備
                rot_mat = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
                # 画像の回転
                img_rot = cv2.warpAffine(img, rot_mat, (lx, ly), flags=cv2.INTER_CUBIC)
                # 回転された画像から、学習用ベクトルの取得
                img_vector = getImageVector(img_rot)
                # 学習用データの格納
                X = np.append(X, img_vector, axis=0)
                y = np.append(y, hand_class)

# ニューラルネットワークによる画像の学習
clf = MLPClassifier(hidden_layer_sizes=(100, ), max_iter=500, tol=0.0001, random_state=None)

print('学習中…')
clf.fit(X, y)

# 学習結果のファイルへの書き出し
joblib.dump(clf, savefile)
print('学習結果はファイル {0} に保存されました'.format(savefile))

# 損失関数のグラフの軸ラベルを設定
plt.xlabel('time step')
plt.ylabel('loss')

# グラフ縦軸の範囲を0以上と定める
plt.ylim(0, max(clf.loss_curve_))

# 損失関数の時間変化を描画
plt.plot(clf.loss_curve_)

# 描画したグラフを表示
plt.show()
