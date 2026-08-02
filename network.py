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
        self.on_move_callback = None

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def create_room(self, on_connected, on_move_received):
        self.on_move_callback = on_move_received
        
        def server_thread():
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("0.0.0.0", PORT))
                server.listen(1)

                self.connection, addr = server.accept()
                self.connected = True

                # 通知主界面：连接成功
                Clock.schedule_once(lambda dt: on_connected(True))
                self.receive_loop()
            except Exception as e:
                print("服务器错误:", e)
                Clock.schedule_once(lambda dt: on_connected(False))

        threading.Thread(target=server_thread, daemon=True).start()
        return self.get_ip()

    def join_room(self, ip, on_connected, on_move_received):
        self.on_move_callback = on_move_received

        def client_thread():
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((ip, PORT))
                self.connected = True

                Clock.schedule_once(lambda dt: on_connected(True))
                self.receive_loop()
            except Exception as e:
                print("连接失败:", e)
                Clock.schedule_once(lambda dt: on_connected(False))

        threading.Thread(target=client_thread, daemon=True).start()

    def send_move(self, row, col):
        if not self.connected:
            return

        try:
            data = f"{row},{col}\n"
            if self.connection:
                self.connection.send(data.encode())
            elif self.socket:
                self.socket.send(data.encode())
        except Exception as e:
            print("发送落子失败:", e)
            self.connected = False

    def receive_loop(self):
        buffer = ""
        while self.connected:
            try:
                if self.connection:
                    data = self.connection.recv(1024)
                else:
                    data = self.socket.recv(1024)

                if not data:
                    self.connected = False
                    break

                buffer += data.decode()

                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    if "," in msg:
                        r, c = map(int, msg.split(","))
                        # 切回 Kivy 主线程更新 UI
                        if self.on_move_callback:
                            Clock.schedule_once(lambda dt, row=r, col=c: self.on_move_callback(row, col))
            except Exception as e:
                print("接收数据异常:", e)
                self.connected = False
                break

    def close(self):
        self.connected = False
        try:
            if self.connection:
                self.connection.close()
            if self.socket:
                self.socket.close()
        except Exception:
            pass
