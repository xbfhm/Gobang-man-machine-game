[app]
title = 五子棋对战
package.name = gomoku
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android 配置
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.build_tools_version = 34.0.0
# 关键修复：只保留 arm64-v8a 架构，解决 armv7a 交叉编译报错并大幅提速
android.archs = arm64-v8a
android.permissions = 

[buildozer]
log_level = 2
warn_on_root = 1
