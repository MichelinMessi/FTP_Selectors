import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import socket
import selectors
import errno


class selectFtpServer:

    def __init__(self):
        self.dic = {}
        self.hasReceived = 0
        self.sel = selectors.DefaultSelector()
        self.create_socket()
        self.handle()

    def create_socket(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 8885))
        server.listen(5)
        server.setblocking(False)
        self.sel.register(server, selectors.EVENT_READ, self.accept)
        print("服务端已开启，等待用户连接...")

    def handle(self):
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def accept(self, sock, mask):

        conn, addr = sock.accept()
        print("from %s %s connected" % addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

        self.dic[conn] = {}

    def read(self, conn, mask):
        try:
            if not self.dic[conn]:

                data = conn.recv(1024)
                cmd, filename, filesize = str(data, encoding='utf-8').split('|')
                self.dic = {conn: {"cmd": cmd, "filename": filename, "filesize": int(filesize)}}

                if cmd == 'put':
                    conn.send(bytes("OK", encoding='utf8'))

                if self.dic[conn]['cmd'] == 'get':
                    file = os.path.join(BASE_DIR, "download", filename)

                    if os.path.exists(file):
                        fileSize = os.path.getsize(file)
                        send_info = '%s|%s' % ('YES', fileSize)
                        conn.send(bytes(send_info, encoding='utf8'))
                    else:
                        send_info = '%s|%s' % ('NO', 0)
                        conn.send(bytes(send_info, encoding='utf8'))
            else:
                if self.dic[conn].get('cmd', None):
                    cmd = self.dic[conn].get('cmd')
                    if hasattr(self, cmd):
                        func = getattr(self, cmd)
                        func(conn)
                    else:
                        print("error cmd!")
                        conn.close()
                else:
                    print("error cmd!")
                    conn.close()

        except Exception as e:
            print('error', e)
            self.sel.unregister(conn)
            conn.close()

    def put(self, conn):

        fileName = self.dic[conn]['filename']
        fileSize = self.dic[conn]['filesize']
        path = os.path.join(BASE_DIR, "upload", fileName)
        recv_data = conn.recv(1024)
        self.hasReceived += len(recv_data)

        with open(path, 'ab') as f:
            f.write(recv_data)
        if fileSize == self.hasReceived:
            if conn in self.dic.keys():
                self.dic[conn] = {}
            print("%s上传完毕！" % fileName)

    def get(self, conn):
        # conn.send(bytes("Hello", encoding="utf-8"))

        filename = self.dic[conn]['filename']
        filesize = os.path.getsize(filename)
        path = os.path.join(BASE_DIR, "download", filename)
        sent_data = 0
        status_code = bytes(conn.recv(1024), encoding='utf8')
        if status_code == "OK":
            # conn.send(bytes(path, encoding="utf-8"))
            with open(path, 'rb', encoding='utf8') as f:
                while filesize > sent_data:
                    contant = f.read(1024)
                    conn.send(contant)
                    sent_data += len(contant)
            self.dic[conn] = {}
            print('%s文件下载完毕' % (filename,))
            # try:
            #     with open(path, 'rb') as f:
            #         # 在此处使用文件
            #         content = f.read(1024)
            #         # print(content)
            #         conn.send(content)
            #         sent_data += len(content)
            #     self.dic[conn] = {}
            #     print('%s文件下载完毕' % (filename,))
            # except FileNotFoundError:
            #     # 文件不存在错误处理
            #     print("File not found: ", filename)
            # except Exception as e:
            #     # 其他文件操作错误处理
            #     print("File error:", e)

        #     # conn.send("OK")
        #     print(str(conn.recv(1024), 'utf-8'))
        #     try:
        #         with open(path, 'rb') as f:
        #             for line in f:
        #                 conn.send(line)
        #         self.dic[conn] = {}
        #         print('文件下载完毕!')

if __name__ == '__main__':
    selectFtpServer()

