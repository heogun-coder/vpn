from flask import Flask, render_template, jsonify, request
import os
import subprocess
import time
from vpn_controller import VPNController

app = Flask(__name__)
vpn_controller = VPNController()

@app.route('/')
def index():
    """메인 페이지"""
    vpn_status = vpn_controller.get_status()
    return render_template('index.html', vpn_status=vpn_status)

@app.route('/status')
def status():
    """VPN 상태 페이지"""
    vpn_status = vpn_controller.get_status()
    return render_template('status.html', vpn_status=vpn_status)

@app.route('/api/status')
def api_status():
    """VPN 상태 API"""
    vpn_status = vpn_controller.get_status()
    return jsonify({
        "status": vpn_status, 
        "connected": vpn_status == "connected",
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/connect', methods=['POST'])
def api_connect():
    """VPN 연결 API"""
    try:
        vpn_controller.connect()
        return jsonify({"success": True, "message": "VPN 연결을 시작했습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": f"VPN 연결 실패: {str(e)}"}), 500

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """VPN 연결 종료 API"""
    try:
        vpn_controller.disconnect()
        return jsonify({"success": True, "message": "VPN 연결을 종료했습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": f"VPN 연결 종료 실패: {str(e)}"}), 500

@app.route('/api/keep_alive', methods=['POST'])
def api_keep_alive():
    """사용자 활성 상태 유지 API"""
    vpn_controller.update_last_activity()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
