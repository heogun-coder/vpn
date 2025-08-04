# WireGuard VPN 관리자

AWS EC2 t2.micro 인스턴스(Amazon Linux 2)에서 WireGuard VPN을 관리하는 Flask 기반 웹 애플리케이션입니다.

## 🎯 주요 기능

- **새로운 피어 생성**: WireGuard 키페어, IP 할당, 설정 파일 자동 생성
- **VPN 상태 확인**: `wg show` 명령어 출력 표시
- **클라이언트 설정 제공**: 복사-붙여넣기 가능한 설정 파일
- **피어 목록 관리**: 등록된 모든 피어 정보 표시

## 🧱 기술 요구사항

- Python 3.11 (Elastic Beanstalk 호환)
- WireGuard CLI 도구
- AWS EC2 t2.micro 인스턴스 (Amazon Linux 2)
- sudo 권한 (WireGuard 설정 변경용)

## 📁 프로젝트 구조

```
vpn/
├── application.py          # Flask 엔트리 포인트
├── wireguard/
│   ├── __init__.py
│   └── manager.py         # WireGuard 로직
├── templates/
│   └── index.html         # 웹 UI
├── requirements.txt        # Python 의존성
└── README.md
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# WireGuard 설치 (Amazon Linux 2)
sudo yum update -y
sudo yum install -y wireguard-tools
```

### 2. 네트워크 설정

```bash
# IP 포워딩 활성화
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# iptables 규칙 설정 (선택사항)
sudo iptables -A FORWARD -i wg0 -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

### 3. 애플리케이션 실행

```bash
# 개발 모드
python application.py

# 프로덕션 모드 (권장)
gunicorn -w 4 -b 0.0.0.0:5000 application:app
```

## 🔧 사용 방법

### 웹 인터페이스 접속

브라우저에서 `http://your-ec2-public-ip:5000` 접속

### 피어 생성

1. "새로운 피어 생성" 버튼 클릭
2. 생성된 설정 파일 복사
3. 클라이언트 기기에서 WireGuard 앱 설치
4. 설정 파일 가져오기 또는 `wg-quick up [파일명]` 실행

### VPN 상태 확인

"VPN 상태 확인" 버튼을 클릭하여 현재 연결된 피어와 트래픽 통계 확인

## ⚠️ 중요 안내

- **피어 생성만으로는 VPN 연결이 되지 않습니다**
- 생성된 설정을 클라이언트 기기에서 사용해야 실제 연결됨
- 연결 후 클라이언트의 공인 IP가 서버 IP로 변경됨
- `AllowedIPs = 0.0.0.0/0`로 모든 트래픽이 VPN을 통해 라우팅됨

## 🔒 보안 고려사항

- 이 애플리케이션은 내부 사용을 위해 설계됨
- 공개 인터넷에 노출 시 인증 추가 필요
- EC2 보안 그룹에서 포트 5000 (웹)과 51820 (WireGuard) 열기

## 📋 설정 파일 예시

### 서버 설정 (`/etc/wireguard/wg0.conf`)
```ini
[Interface]
PrivateKey = [서버 개인키]
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# peer_1
PublicKey = [피어 공개키]
AllowedIPs = 10.0.0.2/32
```

### 클라이언트 설정
```ini
[Interface]
PrivateKey = [클라이언트 개인키]
Address = 10.0.0.2/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = [서버 공개키]
Endpoint = [서버 공인 IP]:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

## 🐛 문제 해결

### WireGuard 인터페이스 생성 실패
```bash
# WireGuard 모듈 로드
sudo modprobe wireguard

# 인터페이스 상태 확인
sudo wg show
```

### 권한 문제
```bash
# 애플리케이션에 sudo 권한 부여
echo "your-user ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/wg-quick, /usr/bin/ip" | sudo tee /etc/sudoers.d/wireguard
```

### 네트워크 연결 문제
```bash
# WireGuard 서비스 상태 확인
sudo systemctl status wg-quick@wg0

# 로그 확인
sudo journalctl -u wg-quick@wg0 -f
```

## 📝 라이선스

MIT License 