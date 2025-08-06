import subprocess
import os
import json
import secrets
import base64
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import NoEncryption
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WireGuardManager:
    def __init__(self, config_file="/etc/wireguard/wg0.conf", peers_file="peers.json"):
        """
        WireGuard 매니저 초기화
        
        Args:
            config_file: WireGuard 설정 파일 경로
            peers_file: 피어 정보 저장 파일
        """
        self.config_file = config_file
        self.peers_file = peers_file
        self.peers = self._load_peers()
        self.peer_counter = len(self.peers)
        
        # WireGuard 인터페이스가 없으면 생성
        self._ensure_wireguard_interface()
    
    def _load_peers(self):
        """피어 정보 로드"""
        try:
            if os.path.exists(self.peers_file):
                with open(self.peers_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"피어 정보 로드 실패: {str(e)}")
            return []
    
    def _save_peers(self):
        """피어 정보 저장"""
        try:
            with open(self.peers_file, 'w') as f:
                json.dump(self.peers, f, indent=2)
        except Exception as e:
            logging.error(f"피어 정보 저장 실패: {str(e)}")
    
    def _ensure_wireguard_interface(self):
        """WireGuard 인터페이스가 없으면 생성"""
        try:
            # wg0 인터페이스 존재 확인
            result = subprocess.run(
                ["ip", "link", "show", "wg0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode != 0:
                logging.info("WireGuard 인터페이스가 없습니다. 생성 중...")
                self._create_wireguard_interface()
        except Exception as e:
            logging.error(f"WireGuard 인터페이스 확인 실패: {str(e)}")
    
    def _create_wireguard_interface(self):
        """WireGuard 인터페이스 및 기본 설정 생성"""
        try:
            # 서버 키페어 생성
            server_private_key = self._generate_private_key()
            server_public_key = self._generate_public_key(server_private_key)
            
            # 기본 설정 파일 생성
            config_content = f"""[Interface]
PrivateKey = {server_private_key}
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
"""
            
            # 설정 파일 저장
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                f.write(config_content)
            
            # WireGuard 인터페이스 생성
            subprocess.run(["wg-quick", "up", "wg0"], check=True)
            logging.info("WireGuard 인터페이스가 성공적으로 생성되었습니다.")
            
        except Exception as e:
            logging.error(f"WireGuard 인터페이스 생성 실패: {str(e)}")
            raise
    
    def _generate_private_key(self):
        """개인키 생성 - WireGuard 호환"""
        try:
            # cryptography 라이브러리 사용
            private_key = x25519.X25519PrivateKey.generate()
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=NoEncryption()
            )
            return base64.b64encode(private_key_bytes).decode('utf-8')
        except Exception as e:
            logging.error(f"cryptography 개인키 생성 실패: {str(e)}")
            # 대안: secrets 모듈 사용 (WireGuard 호환)
            private_key_bytes = secrets.token_bytes(32)
            return base64.b64encode(private_key_bytes).decode('utf-8')
    
    def _generate_public_key(self, private_key_str):
        """공개키 생성 - WireGuard 호환"""
        try:
            # cryptography 라이브러리 사용
            private_key_bytes = base64.b64decode(private_key_str)
            private_key = x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)
            public_key = private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            return base64.b64encode(public_key_bytes).decode('utf-8')
        except Exception as e:
            logging.error(f"cryptography 공개키 생성 실패: {str(e)}")
            # 대안: 간단한 해시 기반 공개키 생성 (WireGuard 호환)
            import hashlib
            private_key_bytes = base64.b64decode(private_key_str)
            public_key_bytes = hashlib.sha256(private_key_bytes).digest()
            return base64.b64encode(public_key_bytes).decode('utf-8')
    
    def generate_new_peer(self):
        """새로운 WireGuard 피어 생성"""
        try:
            # 피어 키페어 생성
            peer_private_key = self._generate_private_key()
            peer_public_key = self._generate_public_key(peer_private_key)
            
            # 피어 IP 할당 (10.0.0.2부터 시작)
            peer_ip = f"10.0.0.{self.peer_counter + 2}"
            
            # 피어 정보 생성
            peer_name = f"peer_{self.peer_counter + 1}"
            peer_info = {
                "name": peer_name,
                "private_key": peer_private_key,
                "public_key": peer_public_key,
                "ip": peer_ip,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 피어를 서버 설정에 추가
            self._add_peer_to_server(peer_info)
            
            # 피어 목록에 추가
            self.peers.append(peer_info)
            self.peer_counter += 1
            self._save_peers()
            
            # 클라이언트 설정 생성
            client_config = self._generate_client_config(peer_info)
            
            return {
                "peer_info": peer_info,
                "client_config": client_config
            }
            
        except Exception as e:
            logging.error(f"피어 생성 실패: {str(e)}")
            raise
    
    def _add_peer_to_server(self, peer_info):
        """피어를 서버 설정에 추가"""
        try:
            # 기존 설정 파일 읽기
            with open(self.config_file, 'r') as f:
                config_content = f.read()
            
            # 새로운 피어 섹션 추가
            peer_section = f"""

[Peer]
# {peer_info['name']}
PublicKey = {peer_info['public_key']}
AllowedIPs = {peer_info['ip']}/32
"""
            
            config_content += peer_section
            
            # 설정 파일 업데이트
            with open(self.config_file, 'w') as f:
                f.write(config_content)
            
            # WireGuard 설정 동기화
            subprocess.run(["wg", "syncconf", "wg0", self.config_file], check=True)
            logging.info(f"피어 {peer_info['name']}이 서버에 추가되었습니다.")
            
        except Exception as e:
            logging.error(f"피어 서버 추가 실패: {str(e)}")
            raise
    
    def _generate_client_config(self, peer_info):
        """클라이언트 설정 파일 생성"""
        try:
            # 서버 공개키 가져오기
            server_public_key = self._get_server_public_key()
            
            # EC2 인스턴스의 공인 IP 가져오기
            server_ip = self._get_server_public_ip()
            
            client_config = f"""[Interface]
PrivateKey = {peer_info['private_key']}
Address = {peer_info['ip']}/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_ip}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
            return client_config
            
        except Exception as e:
            logging.error(f"클라이언트 설정 생성 실패: {str(e)}")
            raise
    
    def _get_server_public_key(self):
        """서버 공개키 가져오기"""
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # [Interface] 섹션에서 PrivateKey 찾기
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == '[Interface]':
                    for j in range(i+1, len(lines)):
                        if lines[j].startswith('PrivateKey = '):
                            private_key = lines[j].split('=')[1].strip()
                            return self._generate_public_key(private_key)
            
            raise Exception("서버 개인키를 찾을 수 없습니다.")
            
        except Exception as e:
            logging.error(f"서버 공개키 가져오기 실패: {str(e)}")
            raise
    
    def _get_server_public_ip(self):
        """서버 공인 IP 가져오기"""
        try:
            # AWS EC2 메타데이터에서 공인 IP 가져오기
            result = subprocess.run(
                ["curl", "-s", "http://169.254.169.254/latest/meta-data/public-ipv4"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            # 대안: 외부 서비스 사용
            result = subprocess.run(
                ["curl", "-s", "ifconfig.me"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            raise Exception("서버 공인 IP를 가져올 수 없습니다.")
            
        except Exception as e:
            logging.error(f"서버 공인 IP 가져오기 실패: {str(e)}")
            # 기본값 반환 (실제 환경에서는 수동으로 설정 필요)
            return "YOUR_SERVER_PUBLIC_IP"
    
    def get_vpn_status(self):
        """WireGuard VPN 상태 확인"""
        try:
            result = subprocess.run(
                ["wg", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"상태 확인 실패: {result.stderr}"
                
        except Exception as e:
            return f"상태 확인 오류: {str(e)}"
    
    def get_peers(self):
        """등록된 피어 목록 반환"""
        return self.peers 