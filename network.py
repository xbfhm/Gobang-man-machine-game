# -*- coding: utf-8 -*-
"""
network.py — 局域网联机（TCP 文本协议）
协议：每行一条消息
  MOVE r,c       落子
  CHAT text      聊天
  RESTART        重开
  QUIT           断开
"""

import socket
import threading
from kivy.clock import Clock

PORT = 8888


class Network:
    def __init__(self):
        self.connection = None      # 服务端视角的客户端 socket
        self.socket = None          # 客户端视角的 socket
        self.connected = False
        self._server_socket = None
        self._is_server = False
        self.on_move_callback = None
        self.on_chat_callback = None
        self.on_quit_callback = None
        self.on_connected_callback = None
        self._lock = threading.Lock()

    def is_server(self):
        return self._is_server

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def create_room(self, on_connected, on_move_received, on_chat_received=None,
                    on_quit=None):
        self._is_server = True
        self.on_connected_callback = on_connected
        self.on_move_callback = on_move_received
        self.on_chat_callback = on_chat_received
        self.on_quit_callback = on_quit

        def server_thread():
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(("0.0.0.0", PORT))
                server.listen(1)
                self._server_socket = server
                conn, addr = server.accept()
                self.connection = conn
                self.connected = True
                Clock.schedule_once(lambda dt: self._safe_call(self.on_connected_callback, True))
                self.receive_loop()
            except Exception as e:
                print("服务器错误:", e)
                Clock.schedule_once(lambda dt: self._safe_call(self.on_connected_callback, False))

        threading.Thread(target=server_thread, daemon=True).start()
        return self.get_ip()

    def join_room(self, ip, on_connected, on_move_received, on_chat_received=None,
                  on_quit=None):
        self._is_server = False
        self.on_connected_callback = on_connected
        self.on_move_callback = on_move_received
        self.on_chat_callback = on_chat_received
        self.on_quit_callback = on_quit

        def client_thread():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((ip, PORT))
                s.settimeout(None)
                self.socket = s
                self.connected = True
                Clock.schedule_once(lambda dt: self._safe_call(self.on_connected_callback, True))
                self.receive_loop()
            except Exception as e:
                print("连接失败:", e)
                Clock.schedule_once(lambda dt: self._safe_call(self.on_connected_callback, False))

        threading.Thread(target=client_thread, daemon=True).start()

    @staticmethod
    def _safe_call(cb, *args):
        try:
            if cb:
                cb(*args)
        except Exception as e:
            print("callback error:", e)

    def _send(self, line):
        with self._lock:
            try:
                data = (line + "\n").encode("utf-8")
                if self.connection:
                    self.connection.send(data)
                elif self.socket:
                    self.socket.send(data)
            except Exception as e:
                print("发送失败:", e)
                self.connected = False

    def send_move(self, row, col):
        self._send("MOVE %d,%d" % (row, col))

    def send_chat(self, text):
        self._send("CHAT " + text.replace("\n", " ")[:200])

    def send_restart(self):
        self._send("RESTART")

    def send_quit(self):
        self._send("QUIT")
        self.close()

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
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self._handle_line(line)
            except Exception as e:
                print("接收异常:", e)
                self.connected = False
                break
        Clock.schedule_once(lambda dt: self._safe_call(self.on_quit_callback))

    def _handle_line(self, line):
        line = line.strip()
        if not line:
            return
        kind, _, rest = line.partition(" ")
        if kind == "MOVE":
            try:
                r, c = map(int, rest.split(","))
                Clock.schedule_once(
                    lambda dt, rr=r, cc=c: self._safe_call(self.on_move_callback, rr, cc))
            except Exception:
                pass
        elif kind == "CHAT":
            text = rest.strip()
            Clock.schedule_once(
                lambda dt, t=text: self._safe_call(self.on_chat_callback, t))
        elif kind == "RESTART":
            Clock.schedule_once(lambda dt: self._safe_call(self.on_quit_callback, "RESTART"))
        elif kind == "QUIT":
            self.connected = False

    def close(self):
        self.connected = False
        try:
            if self.connection:
                self.connection.close()
            if self.socket:
                self.socket.close()
            if self._server_socket:
                self._server_socket.close()
        except Exception:
            pass
