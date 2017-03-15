# -*- coding: utf-8 -*-
import socket
from io import StringIO
import re
import subprocess

try:
    unicode # python2
    def u(str): return str.decode('utf-8')
    pass
except: # python3
    def u(str): return str
    pass

host = '127.0.0.1'
port = 10500
bufsize = 1024

buff = StringIO(u(''))
pattern = r'WHYPO WORD=\"(.*)\" CLASSID'
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    while True:
        data = sock.recv(bufsize)
        buff.write(data.decode('utf-8'))
        data = buff.getvalue().replace('> ', '>\n ')
        if '\n' in data:
            lines = data.splitlines()
            for i in range(len(lines)-1):
                if lines[i] != '.':
                    #print(lines[i])
                    m = re.search(pattern, lines[i])
                    if m:
                        word = m.group(1)
                        # 認識された単語wordの中に、u('...') という文字列が含まれるかどうかを
                        # チェックし、文字列に応じたアクションを記述します。
                        # u('...')でくくるのは、python2とpython3の互換性を保つためです。
                        # 「対象となる文字が含まれているか」を調べていますので、
                        # 先に「『１』が含まれるか」をチェックすると
                        # １０～１２がすべて「１」と判定されてしまいます。
                        # そのため、１０～１２のチェックを先に行っています。

                        if u('１０') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch10']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('１１') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch11']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('１２') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch12']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('１') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch1']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('２') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch2']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('３') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch3']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('４') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch4']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('５') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch5']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('６') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch6']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('７') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch7']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('８') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch8']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('９') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'ch9']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('電源') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'power']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('入力') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'input']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('ボリュームダウン') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'vdown']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('ボリュームアップ') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'vup']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('チャンネルダウン') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'cdown']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')
                        elif u('チャンネルアップ') in word:
                            print(word)
                            args = ['irsend', '-#', '1', 'SEND_ONCE', 'TV', 'cup']
                            try:
                                subprocess.Popen(args)
                            except OSError:
                                print('command not found.')

            buff.close()
            buff = StringIO(u(''))
            if lines[len(lines)-1] != '.':
            	buff.write(lines[len(lines)-1])

except socket.error:
    print('socket error')
except KeyboardInterrupt:
    pass

sock.close()
