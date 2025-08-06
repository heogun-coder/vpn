#!/bin/bash

# WireGuard VPN 서버 설정 스크립트
# AWS EC2 t2.micro (Amazon Linux 2)용

set -e

echo "🚀 WireGuard VPN 서버 설정을 시작합니다..."

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo yum update -y

# 필수 패키지 설치
echo "🔧 필수 패키지 설치 중..."
sudo yum install -y git python3.11 python3.11-pip python3.11-venv wireguard-tools iptables-services firewalld

sudo systemctl start firewalld
sudo systemctl enable firewalld

# IP 포워딩 활성화
echo "🌐 IP 포워딩 활성화 중..."
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# iptables 규칙 설정
echo "🛡️ iptables 규칙 설정 중..."
sudo iptables -A FORWARD -i wg0 -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# iptables 규칙 영구 저장 (Amazon Linux 2)
echo "💾 iptables 규칙 영구 저장 중..."
sudo service iptables save

# 애플리케이션 디렉토리 생성
echo "📁 애플리케이션 디렉토리 설정 중..."
sudo mkdir -p /opt/wireguard-manager
sudo chown $USER:$USER /opt/wireguard-manager

# WireGuard 디렉토리 생성
echo "🔐 WireGuard 디렉토리 생성 중..."
sudo mkdir -p /etc/wireguard
sudo chmod 700 /etc/wireguard

# 애플리케이션에 sudo 권한 부여
echo "🔑 sudo 권한 설정 중..."
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick, /usr/bin/ip, /usr/bin/iptables" | sudo tee /etc/sudoers.d/wireguard

# 방화벽 설정 (EC2 보안 그룹에서도 설정 필요)
echo "🔥 방화벽 설정 중..."
sudo firewall-cmd --permanent --add-port=5000/tcp  # 웹 인터페이스
sudo firewall-cmd --permanent --add-port=51820/udp # WireGuard
sudo firewall-cmd --reload

# 가상환경 생성
echo "🐍 Python 가상환경 생성 중..."
cd /opt/wireguard-manager
python3.11 -m venv venv
source venv/bin/activate

# pip 업그레이드
echo "📦 pip 업그레이드 중..."
pip install --upgrade pip

# 서비스 파일 생성 (가상환경 사용)
echo "⚙️ 서비스 파일 생성 중..."
sudo tee /etc/systemd/system/wireguard-manager.service > /dev/null <<EOF
[Unit]
Description=WireGuard VPN Manager
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/wireguard-manager
Environment=PATH=/opt/wireguard-manager/venv/bin
ExecStart=/opt/wireguard-manager/venv/bin/python application.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
echo "🔄 서비스 활성화 중..."
sudo systemctl daemon-reload
sudo systemctl enable wireguard-manager

echo "✅ 서버 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "1. Git 저장소 클론: git clone [your-repo-url] /opt/wireguard-manager"
echo "2. 가상환경 활성화: source /opt/wireguard-manager/venv/bin/activate"
echo "3. 의존성 설치: pip install -r requirements.txt"
echo "4. 서비스 시작: sudo systemctl start wireguard-manager"
echo "5. http://your-ec2-ip:5000에서 웹 인터페이스 접속"
echo ""
echo "🔒 보안 그룹 설정:"
echo "- 포트 5000 (TCP): 웹 인터페이스"
echo "- 포트 51820 (UDP): WireGuard VPN"
