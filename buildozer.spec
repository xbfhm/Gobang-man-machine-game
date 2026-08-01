[app]
title = 五子棋对战
package.name = gomoku
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.3

# 锁定 requirements
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Android 配置
android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
android.archs = arm64-v8a
android.permissions = 

[buildozer]
log_level = 2
warn_on_root = 1
