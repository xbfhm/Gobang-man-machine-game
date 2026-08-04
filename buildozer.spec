[app]
title = 五子棋对战
package.name = gomoku
package.domain = org.example
source.dir = .

# 加入字体和资源文件支持
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,ttc

version = 0.5

# ===== 关键修改：固定 Python 版本（推荐 3.11）=====
python.version = 3.11

# Python 和 Kivy（此处 kivy 将使用与 Python 3.11 兼容的版本）
requirements = python3,kivy

# 手机方向
orientation = portrait
fullscreen = 0

# =====================
# Android 配置
# =====================
# android.api 推荐使用 30，兼容性更好（也可保留 34）
android.api = 30
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
android.archs = arm64-v8a

# 开启网络权限
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# =====================
# Buildozer 通用配置
# =====================
[buildozer]
log_level = 2
warn_on_root = 1
