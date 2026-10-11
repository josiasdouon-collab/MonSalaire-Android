[app]
title = MON SALAIRE
package.name = monsalairesci
package.domain = ci.monsalaire
source.dir = .
source.include_exts = py,png,jpg,txt,md,ttf
version = 6.0.0
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,sqlite3,certifi,pillow,openssl
orientation = portrait
android.permissions = INTERNET
android.allow_backup = True
fullscreen = 0
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[android]
p4a.branch = v2024.01.21
android.api = 33
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
