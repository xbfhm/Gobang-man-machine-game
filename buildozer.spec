[app]
# =====================================================
# 五子棋豪华版 v2.0 —— 安卓 16 (API 36) 兼容配置
# 关键点：
#   * android.api = 36        （targetSdk = Android 16）
#   * android.ndk = 28c       （NDK r28+ 默认按 16KB 页大小对齐编译，
#                              满足 Google Play 对安卓15+ 的 16KB 要求）
#   * android.archs = arm64-v8a（16KB 对齐仅对 64 位设备强制；只打 64 位包）
#   * p4a.branch = develop    （python-for-android 开发分支，
#                              已修复 16KB 对齐与 API 36 相关兼容问题）
# =====================================================
title = 五子棋豪华版
package.name = gomoku16
package.domain = org.gomoku
source.dir = .

# 打包内容：Python + 字体
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,ttc,json
source.exclude_dirs = tests, .git, .github, __pycache__, .buildozer

version = 2.0

# requirements：python 3.11.7 + kivy 2.3.1 + plyer(震动)
# 注意：必须同时固定 hostpython3 == python3，否则 p4a 会因
# 宿主 Python(默认3.14.2) 与目标 Python(3.11.7) 版本不一致而报错
requirements = python3==3.11.7,hostpython3==3.11.7,kivy==2.3.1,plyer

orientation = portrait
fullscreen = 0

# =====================
# Android 配置（安卓 16）
# =====================
# targetSdkVersion = 36（安卓 16）
android.api = 36
# minSdk = 24（安卓 7.0 及以上；安卓 16 手机远高于此）
android.minapi = 24
# NDK r28c：默认生成 16KB 对齐的 .so
android.ndk = 28c
# NDK 目标 API
android.ndk_api = 24
# 只构建 arm64-v8a（16KB 对齐只要求 64 位；覆盖 99% 以上安卓 16 设备）
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools_version = 36.0.0
android.enable_androidx = True

# 权限：联网 + 震动
android.permissions = INTERNET, ACCESS_NETWORK_STATE, VIBRATE

# python-for-android 使用 develop 分支（含 16KB 修复，配合 NDK r28c）
p4a.branch = develop

# 出错时保留完整日志便于排查
log_level = 2

# =====================
# Buildozer 通用
# =====================
[buildozer]
log_level = 2
warn_on_root = 1
