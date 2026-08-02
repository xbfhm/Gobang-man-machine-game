# -*- coding: utf-8 -*-

import socket
import threading

from kivy.clock import Clock


PORT = 8888



class Network:


    def __init__(self):

        self.connection = None

        self.socket = None

        self.connected = False



    # =====================
    # 获取本机局域网IP
    # =====================

    def get_ip(self):

        try:

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            s.connect(
                ("8.8.8.8",80)
            )


            ip = s.getsockname()[0]


            s.close()


            return ip


        except:


            return "未知IP"




    # =====================
    # 创建房间
    # =====================

    def create_room(self,callback):


        def server_thread():


            try:


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
                        "0.0.0.0",
                        PORT
                    )
                )


                server.listen(1)



                ip=self.get_ip()


                print(
                    "等待连接:",
                    ip
                )



                # 等待玩家加入

                self.connection,addr=server.accept()



                self.connected=True



                print(
                    "连接成功:",
                    addr
                )



                # 通知主界面

                Clock.schedule_once(
                    lambda dt:
                    callback(True)
                )



                self.receive_loop(
                    callback
                )



            except Exception as e:


                print(
                    "服务器错误:",
                    e
                )



        threading.Thread(
            target=server_thread,
            daemon=True
        ).start()



        return self.get_ip()





    # =====================
    # 加入房间
    # =====================


    def join_room(self,ip,callback):


        def client_thread():


            try:


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



                Clock.schedule_once(
                    lambda dt:
                    callback(True)
                )



                self.receive_loop(
                    callback
                )



            except Exception as e:


                print(
                    "连接失败:",
                    e
                )


                Clock.schedule_once(
                    lambda dt:
                    callback(False)
                )




        threading.Thread(
            target=client_thread,
            daemon=True
        ).start()





    # =====================
    # 发送棋子
    # =====================


    def send_move(self,row,col):


        if not self.connected:

            return



        try:


            data=f"{row},{col}\n"



            if self.connection:


                self.connection.send(
                    data.encode()
                )


            elif self.socket:


                self.socket.send(
                    data.encode()
                )



        except:


            self.connected=False






    # =====================
    # 接收循环
    # =====================


    def receive_loop(self,callback):


        buffer=""


        while self.connected:


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


                    self.connected=False

                    break



                buffer+=data.decode()



                while "\n" in buffer:


                    msg,buffer=buffer.split(
                        "\n",
                        1
                    )



                    if "," in msg:


                        r,c=map(
                            int,
                            msg.split(",")
                        )


                        # 回到Kivy主线程

                        Clock.schedule_once(
                            lambda dt:
                            callback(
                                r,
                                c
                            )
                        )



            except:


                self.connected=False

                break





    # =====================
    # 关闭连接
    # =====================


    def close(self):


        self.connected=False


        try:

            if self.connection:

                self.connection.close()


            if self.socket:

                self.socket.close()


        except:

            pass
