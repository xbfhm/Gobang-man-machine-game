# -*- coding: utf-8 -*-

import socket
import threading


PORT = 8888



class Network:


    def __init__(self):

        self.socket = None

        self.connection = None

        self.connected = False



    # =====================
    # 创建房间
    # =====================

    def create_room(self):

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )


        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )


        server.bind(
            (
                "",
                PORT
            )
        )


        server.listen(1)



        # 获取本机IP

        hostname = socket.gethostname()

        ip = socket.gethostbyname(
            hostname
        )


        print(
            "房间IP:",
            ip
        )



        # 等待别人连接

        self.connection,addr = server.accept()


        self.connected=True


        print(
            "玩家加入:",
            addr
        )


        return ip




    # =====================
    # 加入房间
    # =====================


    def join_room(self,ip):

        self.socket=socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )


        self.socket.connect(
            (
                ip,
                PORT
            )
        )


        self.connected=True



    # =====================
    # 发送棋子
    # =====================


    def send_move(self,row,col):

        data=f"{row},{col}"


        if self.connection:

            self.connection.send(
                data.encode("utf-8")
            )


        elif self.socket:

            self.socket.send(
                data.encode("utf-8")
            )




    # =====================
    # 接收棋子
    # =====================


    def receive_move(self):

        try:

            if self.connection:

                data=self.connection.recv(
                    1024
                )

            else:

                data=self.socket.recv(
                    1024
                )


            if not data:

                return None



            r,c=map(
                int,
                data.decode(
                    "utf-8"
                ).split(",")
            )


            return r,c



        except:

            return None




    # =====================
    # 开启监听线程
    # =====================


    def listen(self,callback):


        def run():


            while self.connected:


                move=self.receive_move()


                if move:

                    callback(
                        move[0],
                        move[1]
                    )



        threading.Thread(
            target=run,
            daemon=True
        ).start()
