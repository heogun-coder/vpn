import subprocess
import os
import time
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VPNController:
    def __init__(self, config_file="/etc/openvpn/client/client.ovpn", inactivity_timeout=300):
        """
        VPN 컨트롤러 초기화
        
        Args:
            config_file: OpenVPN 설정 파일 경로
            inactivity_timeout: 비활성 시간 제한(초), 기본 5분
        """
        self.config_file = config_file
        self.status = "disconnected"
        self.vpn_process = None
        self.last_activity = time.time()
        self.inactivity_timeout = inactivity_timeout
        
        # 비활성 체크 스레드 시작
        self.inactivity_thread = threading.Thread(target=self._check_inactivity, daemon=True)
        self.inactivity_thread.start()
    
    def connect(self):
        """VPN 연결 시작"""
        if self.status == "connected":
            logging.info("VPN already connected")
            return
        
        try:
            # VPN 프로세스 시작
            self.vpn_process = subprocess.Popen(
                ["sudo", "openvpn", "--config", self.config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 연결 상태 확인을 위한 시간
            time.sleep(5)
            
            if self.vpn_process.poll() is None:  # 프로세스가 실행 중이면
                self.status = "connected"
                logging.info("VPN connected successfully")
                self.update_last_activity()
            else:
                error = self.vpn_process.stderr.read().decode()
                logging.error(f"VPN connection failed: {error}")
                raise Exception("VPN connection failed")
        except Exception as e:
            logging.error(f"Error connecting to VPN: {str(e)}")
            self.status = "disconnected"
            raise

    def disconnect(self):
        """VPN 연결 종료"""
        if self.status == "disconnected":
            return
        
        try:
            if self.vpn_process and self.vpn_process.poll() is None:
                # VPN 프로세스 종료
                subprocess.run(["sudo", "killall", "openvpn"], check=True)
                self.vpn_process = None
            
            self.status = "disconnected"
            logging.info("VPN disconnected")
        except Exception as e:
            logging.error(f"Error disconnecting from VPN: {str(e)}")
            raise

    def get_status(self):
        """VPN 상태 확인"""
        # openvpn 프로세스가 실행 중인지 확인
        try:
            result = subprocess.run(
                ["pgrep", "openvpn"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                self.status = "connected"
            else:
                self.status = "disconnected"
        except Exception:
            self.status = "disconnected"
            
        return self.status
    
    def update_last_activity(self):
        """사용자 활동 시간 업데이트"""
        self.last_activity = time.time()
        logging.debug("Activity timestamp updated")
    
    def _check_inactivity(self):
        """비활성 시간 체크 및 자동 연결 해제 스레드"""
        while True:
            try:
                if self.status == "connected":
                    elapsed = time.time() - self.last_activity
                    if elapsed > self.inactivity_timeout:
                        logging.info(f"Inactivity timeout reached ({self.inactivity_timeout}s). Disconnecting VPN.")
                        self.disconnect()
            except Exception as e:
                logging.error(f"Error in inactivity check: {str(e)}")
            
            time.sleep(10)  # 10초마다 체크
