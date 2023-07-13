import socket
import os, sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class selectFtpClient:

    def __init__(self):
        self.sk = None
        self.args = sys.argv
        if len(self.args) > 1:
            self.port = (self.args[1], int(self.args[2]))
        else:
            self.port = ("127.0.0.1", 8885)
        self.create_socket()
        self.command_fanout()

    def create_socket(self):
        try:
            self.sk = socket.socket()
            self.sk.connect(self.port)
            print('连接FTP服务器成功!')
        except Exception as e:
            print("error: ", e)

    def command_fanout(self):
        while True:
            cmd = input('>>>').strip()
            if cmd == 'exit()':
                break
            cmd, file = cmd.split()
            if hasattr(self, cmd):
                func = getattr(self, cmd)
                func(cmd, file)
            else:
                print('调用错误!')

    def put(self, cmd, file):

        if os.path.isfile(file):
            fileName = os.path.basename(file)
            fileSize = os.path.getsize(file)
            fileInfo = '%s|%s|%s' % (cmd, fileName, fileSize)
            self.sk.send(bytes(fileInfo, encoding='utf8'))
            recvStatus = self.sk.recv(1024)
            # print('recvStatus', recvStatus)
            hasSend = 0
            if str(recvStatus, encoding='utf8') == "OK":
                with open(file, 'rb') as f:
                    while fileSize > hasSend:
                        contant = f.read(1024)
                        recv_size = len(contant)
                        self.sk.send(contant)
                        hasSend += recv_size
                        s = str(int(hasSend / fileSize * 100)) + "%"
                        print("正在上传文件：" + fileName + "   已经上传：" + s)
                print('%s文件上传完毕' % (fileName,))
        else:
            print('文件不存在')

    def get(self, cmd, file):
        fileInfo = '%s|%s|%s' % (cmd, file, '0')
        self.sk.send(bytes(fileInfo, encoding='utf8'))

        backInfo = self.sk.recv(1024)
        status_code, filesize = str(backInfo, encoding='utf8').split('|')
        filesize = int(filesize)
        recived_size = 0

        if status_code == "YES":
            send_status = "OK"
            self.sk.send(bytes(send_status, encoding='utf8'))
            print("开始下载")
            path = os.path.join(BASE_DIR, "download", file)
            data = self.sk.recv(1024)
            recived_size += len(data)
            with open(path, 'ab') as f:
                while recived_size < filesize:
                    f.write(data)
                    s = str(int(recived_size / filesize * 100)) + "%"
                    print("正在下载文件：" + str(file) + "   已经下载：" + s)
            print("%s 下载完毕" % str(file))
        elif status_code == "NO":
            print("%s 文件不存在" % str(file))

if __name__ == '__main__':
    selectFtpClient()
