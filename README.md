# WireGuard VPN 관리자

AWS EC2 t2.micro 인스턴스(Amazon Linux 2)에서 WireGuard VPN을 관리하는 Flask 기반 웹 애플리케이션입니다.

## 🎯 주요 기능

- **새로운 피어 생성**: WireGuard 키페어, IP 할당, 설정 파일 자동 생성
- **VPN 상태 확인**: `wg show` 명령어 출력 표시 (실패 시 설정 파일 기반 정보)
- **클라이언트 설정 제공**: 복사-붙여넣기 가능한 설정 파일
- **피어 목록 관리**: 등록된 모든 피어 정보 표시
- **설정 파일 내보내기**: 서버 WireGuard 설정 파일 확인
- **강화된 오류 처리**: 권한 문제 및 명령어 실행 실패에 대한 대안 제공

## 🧱 기술 요구사항

- Python 3.11 (Elastic Beanstalk 호환)
- WireGuard CLI 도구 (선택사항)
- AWS EC2 t2.micro 인스턴스 (Amazon Linux 2)
- Git (배포용)

## 📁 프로젝트 구조

```
vpn/
├── application.py          # Flask 엔트리 포인트 (강화된 오류 처리)
├── wireguard/
│   ├── __init__.py
│   └── manager.py         # WireGuard 로직 (권한 문제 해결)
├── templates/
│   └── index.html         # 개선된 웹 UI
├── requirements.txt        # Python 의존성
├── setup_server.sh        # 서버 초기 설정
├── deploy.sh              # Git 배포 스크립트
└── README.md
```

## 🚀 설치 및 실행

### 1. 서버 초기 설정

```bash
# 서버 설정 스크립트 실행
sudo bash setup_server.sh
```

이 스크립트는 다음을 수행합니다:
- 시스템 패키지 업데이트
- WireGuard, Python 3.11, Git 설치
- IP 포워딩 활성화
- iptables 규칙 설정
- 가상환경 생성
- systemd 서비스 설정

### 2. Git을 통한 배포

#### 방법 1: 자동 배포 스크립트 사용
```bash
# 저장소 URL 지정하여 배포
sudo bash deploy.sh https://github.com/your-username/wireguard-manager.git

# 또는 기본 URL 사용 (스크립트 내부 설정)
sudo bash deploy.sh
```

#### 방법 2: 수동 배포
```bash
# 애플리케이션 디렉토리로 이동
cd /opt/wireguard-manager

# Git 저장소 클론
git clone https://github.com/your-username/wireguard-manager.git .

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python application.py
```

### 3. 서비스 관리

```bash
# 서비스 시작
sudo systemctl start wireguard-manager

# 서비스 중지
sudo systemctl stop wireguard-manager

# 서비스 재시작
sudo systemctl restart wireguard-manager

# 서비스 상태 확인
sudo systemctl status wireguard-manager

# 로그 확인
sudo journalctl -u wireguard-manager -f
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

### 설정 파일 관리

"설정 파일 내보내기" 버튼을 클릭하여 서버 WireGuard 설정 파일 확인 및 복사

## 🔧 권한 문제 해결

### 설정 파일 위치
- **기본 위치**: `~/wireguard-manager/wg0.conf` (사용자 홈 디렉토리)
- **권한 문제 없음**: `/etc/wireguard/` 접근 불필요
- **자동 생성**: 필요한 모든 디렉토리 자동 생성

### WireGuard 명령어 실행
- **선택적 실행**: `wg`, `wg-quick` 명령어가 없어도 작동
- **대안 제공**: 명령어 실행 실패 시 설정 파일 기반 정보 표시
- **안전한 실행**: 모든 subprocess 호출에 타임아웃 및 예외 처리

## ⚠️ 중요 안내

- **피어 생성만으로는 VPN 연결이 되지 않습니다**
- 생성된 설정을 클라이언트 기기에서 사용해야 실제 연결됨
- 연결 후 클라이언트의 공인 IP가 서버 IP로 변경됨
- `AllowedIPs = 0.0.0.0/0`로 모든 트래픽이 VPN을 통해 라우팅됨

## 🔒 보안 고려사항

- 이 애플리케이션은 내부 사용을 위해 설계됨
- 공개 인터넷에 노출 시 인증 추가 필요
- EC2 보안 그룹에서 포트 5000 (웹)과 51820 (WireGuard) 열기
- 설정 파일은 사용자 홈 디렉토리에 안전하게 저장

## 📋 설정 파일 예시

### 서버 설정 (자동 생성됨)
```ini
[Interface]
PrivateKey = [서버 개인키]
Address = 10.0.0.1/24
ListenPort = 51820
# PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# peer_1 - 2024-01-15 10:30:00
PublicKey = [피어 공개키]
AllowedIPs = 10.0.0.2/32
```

### 클라이언트 설정 (자동 생성됨)
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

### 가상환경 문제
```bash
# 가상환경 재생성
cd /opt/wireguard-manager
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 권한 문제 (해결됨)
- ✅ 설정 파일이 사용자 디렉토리에 저장됨
- ✅ `/etc/wireguard/` 접근 불필요
- ✅ sudo 권한 없이도 작동

### WireGuard 명령어 문제 (해결됨)
- ✅ 명령어 없어도 기본 기능 작동
- ✅ 대안 방법으로 정보 제공
- ✅ 안전한 명령어 실행 및 타임아웃

### cryptography 라이브러리 문제 (해결됨)
- ✅ 최신 버전 호환성 확보
- ✅ 실패 시 `secrets` 모듈 대안 사용
- ✅ WireGuard 호환 키 생성

### 네트워크 연결 문제
```bash
# 애플리케이션 로그 확인
sudo journalctl -u wireguard-manager -f

# 직접 실행하여 디버그
cd /opt/wireguard-manager
source venv/bin/activate
python application.py
```

### Git 배포 문제
```bash
# Git 저장소 상태 확인
cd /opt/wireguard-manager
git status
git log --oneline -5

# 강제 업데이트
git fetch origin
git reset --hard origin/main
```

## 🚀 개선된 기능

### 1. 권한 문제 완전 해결
- 사용자 디렉토리 사용으로 권한 문제 제거
- 모든 파일 작업이 사용자 권한으로 실행

### 2. 강화된 오류 처리
- 모든 subprocess 호출에 타임아웃 설정
- 명령어 실행 실패 시 대안 방법 제공
- 상세한 로깅 및 예외 처리

### 3. 개선된 사용자 경험
- 실시간 시스템 상태 표시
- 설정 파일 내보내기 기능
- 더 나은 UI/UX 및 피드백

### 4. 안정성 향상
- 캐시된 서버 IP로 성능 향상
- 여러 IP 조회 방법으로 안정성 확보
- 설정 파일 기반 백업 정보 제공

## 📝 라이선스

MIT License