from flask import Flask, render_template, jsonify, request
import os
import subprocess
import time
from wireguard.manager import WireGuardManager

app = Flask(__name__)
wg_manager = WireGuardManager()

@app.route('/')
def index():
    """메인 페이지 - WireGuard VPN 관리"""
    return render_template('index.html')

@app.route('/api/generate_peer', methods=['POST'])
def generate_peer():
    """새로운 WireGuard 피어 생성"""
    try:
        peer_config = wg_manager.generate_new_peer()
        return jsonify({
            "success": True,
            "peer_config": peer_config,
            "message": "새로운 피어가 성공적으로 생성되었습니다."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"피어 생성 실패: {str(e)}"
        }), 500

@app.route('/api/vpn_status')
def vpn_status():
    """WireGuard VPN 상태 확인"""
    try:
        status_output = wg_manager.get_vpn_status()
        return jsonify({
            "success": True,
            "status_output": status_output,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"상태 확인 실패: {str(e)}"
        }), 500

@app.route('/api/peers')
def get_peers():
    """등록된 피어 목록 조회"""
    try:
        peers = wg_manager.get_peers()
        return jsonify({
            "success": True,
            "peers": peers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"피어 목록 조회 실패: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 