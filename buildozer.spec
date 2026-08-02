[app]
title = 五子棋对战
package.name = gomoku
package.domain = org.example
source.dir = .

# 加入字体和资源文件支持
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,ttc

version = 0.4

# Python 和 Kivy
requirements = python3,kivy

# 手机方向
orientation = portrait
fullscreen = 0

# =====================
# Android 配置
# =====================
android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
android.archs = arm64-v8a

# 开启网络权限（修复打包 TypeError 报错，并开启联网）
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# =====================
# Buildozer配置
# =====================
[buildozer]
log_level = 2
warn_on_root = 1
