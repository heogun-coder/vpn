#!/bin/bash

# WireGuard VPN 관리자 배포 스크립트
# Git을 통한 자동 배포

set -e

# 설정 변수
REPO_URL=${1:-"https://github.com/your-username/wireguard-manager.git"}
APP_DIR="/opt/wireguard-manager"
VENV_DIR="$APP_DIR/venv"

echo "🚀 WireGuard VPN 관리자 배포를 시작합니다..."

# 애플리케이션 디렉토리로 이동
cd $APP_DIR

# Git 저장소 클론 또는 업데이트
if [ -d ".git" ]; then
    echo "📥 Git 저장소 업데이트 중..."
    git pull origin main
else
    echo "📥 Git 저장소 클론 중..."
    git clone $REPO_URL .
fi

# 가상환경 확인 및 생성
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 가상환경 생성 중..."
    python3.11 -m venv $VENV_DIR
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source $VENV_DIR/bin/activate

# 의존성 설치
echo "📦 Python 의존성 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 파일 권한 설정
echo "🔐 파일 권한 설정 중..."
sudo chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/application.py

# 서비스 재시작
echo "🔄 서비스 재시작 중..."
sudo systemctl restart wireguard-manager

# 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sudo systemctl status wireguard-manager --no-pager

echo "✅ 배포가 완료되었습니다!"
echo ""
echo "🌐 웹 인터페이스: http://$(curl -s ifconfig.me):5000"
echo "📋 로그 확인: sudo journalctl -u wireguard-manager -f" 