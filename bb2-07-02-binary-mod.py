# -*- coding: utf-8 -*-
import picamera
import picamera.array
import cv2

with picamera.PiCamera() as camera:
    with picamera.array.PiRGBArray(camera) as stream:
        camera.resolution = (320, 240)

        while True:
            # stream.arrayにBGRの順で映像データを格納
            camera.capture(stream, 'bgr', use_video_port=True)
            # 映像データをグレースケール画像grayに変換
            gray = cv2.cvtColor(stream.array, cv2.COLOR_BGR2GRAY)
            # 画像の二値化 (閾値127)
            (ret, binary) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            # 画像の二値化 (大津の方法)
            #(ret, binary) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            # retの表示
            print(ret)
            # binaryをウインドウに表示
            cv2.imshow('frame', binary)

            # "q"を入力でアプリケーション終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # streamをリセット
            stream.seek(0)
            stream.truncate()

        cv2.destroyAllWindows()
