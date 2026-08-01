[app]
title = 五子棋对战
package.name = gomoku
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# 关键修改：锁定底层 python3 为稳定版本，防止自动下载 Python 3.14 导致 openssl/crypto 编译崩溃
requirements = python3==3.10.12,kivy

orientation = portrait
fullscreen = 0

# Android 配置
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
# 只保留 arm64-v8a 现代架构，速度最快
android.archs = arm64-v8a
android.permissions = 

[buildozer]
log_level = 2
warn_on_root = 1
