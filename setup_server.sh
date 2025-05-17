#!/bin/bash

# EC2 인스턴스 초기 설정 및 OpenVPN + Flask 웹 서버 설치 스크립트
# 사용법: sudo bash setup_server.sh

# 로그 파일 설정
LOG_FILE="/var/log/vpn_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "==== EC2 인스턴스 + OpenVPN + Flask 웹 서버 설치 스크립트 시작 ===="
echo "현재 시간: $(date)"

# 시스템 업데이트
echo "시스템 패키지 업데이트 중..."
yum update -y

# 필요한 패키지 설치
echo "필수 패키지 설치 중..."
yum install -y python3 python3-pip git nano wget unzip

# OpenVPN 설치
echo "OpenVPN 설치 중..."
amazon-linux-extras install -y epel
yum install -y openvpn easy-rsa

# Flask 애플리케이션 디렉토리 생성
echo "Flask 애플리케이션 디렉토리 설정 중..."
mkdir -p /opt/vpn_webapp
cd /opt/vpn_webapp

# 필요한 Python 패키지 설치
echo "Flask 및 필요한 Python 패키지 설치 중..."
pip3 install flask

# 방화벽 설정
echo "방화벽 설정 중..."
if command -v firewall-cmd &> /dev/null; then
    # Firewalld가 설치된 경우
    systemctl start firewalld
    systemctl enable firewalld
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-port=5000/tcp
    firewall-cmd --permanent --add-port=1194/udp
    firewall-cmd --reload
    echo "방화벽 설정 완료"
else
    # iptables 사용
    yum install -y iptables-services
    systemctl start iptables
    systemctl enable iptables
    iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    iptables -A INPUT -p udp --dport 1194 -j ACCEPT
    service iptables save
    echo "iptables 설정 완료"
fi

# OpenVPN 디렉토리 준비
echo "OpenVPN 설정 디렉토리 준비 중..."
mkdir -p /etc/openvpn/client
mkdir -p /etc/openvpn/easy-rsa
cp -r /usr/share/easy-rsa/3/* /etc/openvpn/easy-rsa/

echo "==== 설치 스크립트 완료 ===="
echo "다음 단계:"
echo "1. OpenVPN 서버 구성 파일을 생성하세요"
echo "2. easy-rsa를 사용하여 인증서를 생성하세요"
echo "3. Flask 애플리케이션 파일을 /opt/vpn_webapp에 배치하고 실행하세요"
echo ""
echo "Flask 웹 애플리케이션을 실행하려면:"
echo "cd /opt/vpn_webapp && python3 app.py"