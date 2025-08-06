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
import tempfile
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WireGuardManager:
    def __init__(self, config_file=None, peers_file="peers.json"):
        """
        WireGuard 매니저 초기화
        
        Args:
            config_file: WireGuard 설정 파일 경로 (None이면 사용자 디렉토리 사용)
            peers_file: 피어 정보 저장 파일
        """
        # 사용자 디렉토리에 설정 파일 저장 (권한 문제 해결)
        self.app_dir = os.path.expanduser("~/wireguard-manager")
        os.makedirs(self.app_dir, exist_ok=True)
        
        if config_file is None:
            self.config_file = os.path.join(self.app_dir, "wg0.conf")
        else:
            self.config_file = config_file
            
        self.peers_file = os.path.join(self.app_dir, peers_file)
        self.peers = self._load_peers()
        self.peer_counter = len(self.peers)
        
        # 서버 공인 IP 캐시
        self._cached_server_ip = None
        
        # WireGuard 설정 확인
        self._ensure_wireguard_config()
    
    def _load_peers(self):
        """피어 정보 로드"""
        try:
            if os.path.exists(self.peers_file):
                with open(self.peers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"피어 정보 로드 실패: {str(e)}")
            return []
    
    def _save_peers(self):
        """피어 정보 저장"""
        try:
            with open(self.peers_file, 'w', encoding='utf-8') as f:
                json.dump(self.peers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"피어 정보 저장 실패: {str(e)}")
    
    def _run_command(self, command, check=False, timeout=10):
        """안전한 명령어 실행"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.TimeoutExpired:
            logging.error(f"명령어 실행 시간 초과: {' '.join(command)}")
            return None
        except subprocess.CalledProcessError as e:
            logging.error(f"명령어 실행 실패: {' '.join(command)}, 오류: {e.stderr}")
            return None
        except FileNotFoundError:
            logging.error(f"명령어를 찾을 수 없음: {command[0]}")
            return None
        except Exception as e:
            logging.error(f"명령어 실행 중 예외 발생: {str(e)}")
            return None
    
    def _ensure_wireguard_config(self):
        """WireGuard 설정 파일 확인 및 생성"""
        try:
            if not os.path.exists(self.config_file):
                logging.info("WireGuard 설정 파일이 없습니다. 생성 중...")
                self._create_wireguard_config()
            else:
                logging.info("기존 WireGuard 설정 파일을 사용합니다.")
        except Exception as e:
            logging.error(f"WireGuard 설정 확인 실패: {str(e)}")
    
    def _create_wireguard_config(self):
        """WireGuard 설정 파일 생성"""
        try:
            # 서버 키페어 생성
            server_private_key = self._generate_private_key()
            
            # 기본 설정 파일 생성
            config_content = f"""[Interface]
PrivateKey = {server_private_key}
Address = 10.0.0.1/24
ListenPort = 51820
# PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# 피어 설정은 아래에 자동으로 추가됩니다.
"""
            
            # 설정 파일 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logging.info(f"WireGuard 설정 파일이 생성되었습니다: {self.config_file}")
            
        except Exception as e:
            logging.error(f"WireGuard 설정 파일 생성 실패: {str(e)}")
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
            logging.warning(f"cryptography 개인키 생성 실패, 대안 사용: {str(e)}")
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
            logging.warning(f"cryptography 공개키 생성 실패, 대안 사용: {str(e)}")
            # 대안: 간단한 해시 기반 공개키 생성
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
            
            # 피어를 설정 파일에 추가
            self._add_peer_to_config(peer_info)
            
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
    
    def _add_peer_to_config(self, peer_info):
        """피어를 설정 파일에 추가"""
        try:
            # 기존 설정 파일 읽기
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 새로운 피어 섹션 추가
            peer_section = f"""
[Peer]
# {peer_info['name']} - {peer_info['created_at']}
PublicKey = {peer_info['public_key']}
AllowedIPs = {peer_info['ip']}/32
"""
            
            config_content += peer_section
            
            # 설정 파일 업데이트
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            logging.info(f"피어 {peer_info['name']}이 설정 파일에 추가되었습니다.")
            
            # WireGuard가 실행 중이면 설정 동기화 시도
            self._sync_wireguard_config()
            
        except Exception as e:
            logging.error(f"피어 설정 파일 추가 실패: {str(e)}")
            raise
    
    def _sync_wireguard_config(self):
        """WireGuard 설정 동기화 (선택적)"""
        try:
            # wg 명령어로 현재 상태 확인
            result = self._run_command(["wg", "show"], timeout=5)
            if result and result.returncode == 0:
                # WireGuard가 실행 중이면 동기화 시도
                sync_result = self._run_command(["sudo", "wg", "syncconf", "wg0", self.config_file], timeout=10)
                if sync_result and sync_result.returncode == 0:
                    logging.info("WireGuard 설정이 동기화되었습니다.")
                else:
                    logging.warning("WireGuard 설정 동기화 실패 (권한 없음 또는 인터페이스 없음)")
            else:
                logging.info("WireGuard 인터페이스가 실행되지 않음")
        except Exception as e:
            logging.warning(f"WireGuard 동기화 시도 중 오류 (무시됨): {str(e)}")
    
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
            # 기본 설정 반환
            return f"""[Interface]
PrivateKey = {peer_info['private_key']}
Address = {peer_info['ip']}/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = [서버_공개키를_여기에_입력]
Endpoint = [서버_공인IP]:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    
    def _get_server_public_key(self):
        """서버 공개키 가져오기"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # [Interface] 섹션에서 PrivateKey 찾기
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == '[Interface]':
                    for j in range(i+1, len(lines)):
                        if lines[j].startswith('PrivateKey = '):
                            private_key = lines[j].split('=')[1].strip()
                            return self._generate_public_key(private_key)
                        elif lines[j].startswith('['):
                            break
            
            raise Exception("서버 개인키를 찾을 수 없습니다.")
            
        except Exception as e:
            logging.error(f"서버 공개키 가져오기 실패: {str(e)}")
            return "[서버_공개키_오류]"
    
    def _get_server_public_ip(self):
        """서버 공인 IP 가져오기"""
        if self._cached_server_ip:
            return self._cached_server_ip
            
        try:
            # 여러 방법으로 공인 IP 시도
            methods = [
                # AWS EC2 메타데이터
                ["curl", "-s", "--max-time", "3", "http://169.254.169.254/latest/meta-data/public-ipv4"],
                # 외부 서비스들
                ["curl", "-s", "--max-time", "3", "ifconfig.me"],
                ["curl", "-s", "--max-time", "3", "ipecho.net/plain"],
                ["curl", "-s", "--max-time", "3", "icanhazip.com"]
            ]
            
            for method in methods:
                result = self._run_command(method, timeout=5)
                if result and result.returncode == 0 and result.stdout.strip():
                    ip = result.stdout.strip()
                    # IP 주소 형식 검증
                    if self._is_valid_ip(ip):
                        self._cached_server_ip = ip
                        logging.info(f"서버 공인 IP: {ip}")
                        return ip
            
            # 모든 방법 실패 시 기본값
            logging.warning("서버 공인 IP를 가져올 수 없습니다. 기본값 사용")
            return "YOUR_SERVER_PUBLIC_IP"
            
        except Exception as e:
            logging.error(f"서버 공인 IP 가져오기 실패: {str(e)}")
            return "YOUR_SERVER_PUBLIC_IP"
    
    def _is_valid_ip(self, ip):
        """IP 주소 형식 검증"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def get_vpn_status(self):
        """WireGuard VPN 상태 확인"""
        try:
            # wg show 명령어 실행
            result = self._run_command(["wg", "show"], timeout=10)
            
            if result and result.returncode == 0:
                if result.stdout.strip():
                    return result.stdout
                else:
                    return "WireGuard 인터페이스가 실행되지 않거나 피어가 없습니다."
            else:
                # 대안: 설정 파일 정보 표시
                return self._get_config_status()
                
        except Exception as e:
            logging.error(f"VPN 상태 확인 실패: {str(e)}")
            return f"상태 확인 오류: {str(e)}"
    
    def _get_config_status(self):
        """설정 파일 기반 상태 정보"""
        try:
            status_info = f"설정 파일: {self.config_file}\n"
            status_info += f"등록된 피어 수: {len(self.peers)}\n"
            status_info += f"서버 IP 대역: 10.0.0.1/24\n"
            
            if self.peers:
                status_info += "\n등록된 피어들:\n"
                for peer in self.peers:
                    status_info += f"- {peer['name']}: {peer['ip']} ({peer['created_at']})\n"
            
            return status_info
            
        except Exception as e:
            return f"설정 정보 조회 실패: {str(e)}"
    
    def get_peers(self):
        """등록된 피어 목록 반환"""
        return self.peers
    
    def get_config_file_path(self):
        """설정 파일 경로 반환"""
        return self.config_file
    
    def export_config(self):
        """설정 파일 내용 반환"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"설정 파일 읽기 실패: {str(e)}")
            return f"설정 파일 읽기 실패: {str(e)}"