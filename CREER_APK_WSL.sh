#!/bin/bash
# Lancer depuis le dossier du projet :  bash CREER_APK_WSL.sh
# (le script copie lui-meme le projet dans Ubuntu : ~/monsalaire)
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip curl autoconf automake libtool libltdl-dev \
  pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev libsqlite3-dev build-essential \
  || sudo apt install -y git zip unzip openjdk-21-jdk python3-pip curl autoconf automake libtool libltdl-dev \
  pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev libsqlite3-dev build-essential
# copie du projet dans le disque Linux (obligatoire, /mnt/c ne marche pas)
mkdir -p ~/monsalaire
cp -r "$SRC"/. ~/monsalaire/
cd ~/monsalaire
# Python 3.11 (les versions recentes d'Ubuntu ont un Python trop recent pour buildozer)
pip install --user --break-system-packages uv 2>/dev/null || pip install --user uv
export PATH="$HOME/.local/bin:$PATH"
uv venv --seed --python 3.11 ~/venv_apk
source ~/venv_apk/bin/activate
uv pip install buildozer "cython<3" setuptools
buildozer -v android debug
echo
echo "APK pret : ~/monsalaire/bin/"
ls -la ~/monsalaire/bin/*.apk
mkdir -p /mnt/c/Users/Public/Downloads 2>/dev/null && cp ~/monsalaire/bin/*.apk /mnt/c/Users/Public/Downloads/ 2>/dev/null \
  && echo "Copie aussi dans C:\\Users\\Public\\Downloads" || true
