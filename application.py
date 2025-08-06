from flask import Flask, render_template, jsonify, request
import os
import subprocess
import time
import logging
from wireguard.manager import WireGuardManager

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# WireGuard 매니저 초기화 (오류 처리 포함)
try:
    wg_manager = WireGuardManager()
    logging.info("WireGuard 매니저가 성공적으로 초기화되었습니다.")
except Exception as e:
    logging.error(f"WireGuard 매니저 초기화 실패: {str(e)}")
    wg_manager = None

@app.route('/')
def index():
    """메인 페이지 - WireGuard VPN 관리"""
    try:
        # 매니저 상태 확인
        manager_status = "정상" if wg_manager else "초기화 실패"
        config_path = wg_manager.get_config_file_path() if wg_manager else "N/A"
        
        return render_template('index.html', 
                             manager_status=manager_status,
                             config_path=config_path)
    except Exception as e:
        logging.error(f"메인 페이지 로드 실패: {str(e)}")
        return render_template('index.html', 
                             manager_status="오류",
                             config_path="N/A")

@app.route('/api/generate_peer', methods=['POST'])
def generate_peer():
    """새로운 WireGuard 피어 생성"""
    if not wg_manager:
        return jsonify({
            "success": False,
            "message": "WireGuard 매니저가 초기화되지 않았습니다."
        }), 500
    
    try:
        peer_config = wg_manager.generate_new_peer()
        
        # 추가 정보 포함
        response_data = {
            "success": True,
            "peer_config": peer_config,
            "message": "새로운 피어가 성공적으로 생성되었습니다.",
            "config_file_path": wg_manager.get_config_file_path(),
            "total_peers": len(wg_manager.get_peers())
        }
        
        logging.info(f"피어 생성 성공: {peer_config['peer_info']['name']}")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"피어 생성 실패: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/api/vpn_status')
def vpn_status():
    """WireGuard VPN 상태 확인"""
    if not wg_manager:
        return jsonify({
            "success": False,
            "message": "WireGuard 매니저가 초기화되지 않았습니다."
        }), 500
    
    try:
        status_output = wg_manager.get_vpn_status()
        
        return jsonify({
            "success": True,
            "status_output": status_output,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config_file_path": wg_manager.get_config_file_path(),
            "total_peers": len(wg_manager.get_peers())
        })
        
    except Exception as e:
        error_msg = f"상태 확인 실패: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/api/peers')
def get_peers():
    """등록된 피어 목록 조회"""
    if not wg_manager:
        return jsonify({
            "success": False,
            "message": "WireGuard 매니저가 초기화되지 않았습니다."
        }), 500
    
    try:
        peers = wg_manager.get_peers()
        return jsonify({
            "success": True,
            "peers": peers,
            "total_count": len(peers),
            "config_file_path": wg_manager.get_config_file_path()
        })
        
    except Exception as e:
        error_msg = f"피어 목록 조회 실패: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/api/export_config')
def export_config():
    """설정 파일 내용 내보내기"""
    if not wg_manager:
        return jsonify({
            "success": False,
            "message": "WireGuard 매니저가 초기화되지 않았습니다."
        }), 500
    
    try:
        config_content = wg_manager.export_config()
        return jsonify({
            "success": True,
            "config_content": config_content,
            "config_file_path": wg_manager.get_config_file_path()
        })
        
    except Exception as e:
        error_msg = f"설정 파일 내보내기 실패: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

@app.route('/api/health')
def health_check():
    """애플리케이션 상태 확인"""
    try:
        health_info = {
            "success": True,
            "status": "healthy",
            "manager_initialized": wg_manager is not None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if wg_manager:
            health_info.update({
                "config_file_exists": os.path.exists(wg_manager.get_config_file_path()),
                "config_file_path": wg_manager.get_config_file_path(),
                "total_peers": len(wg_manager.get_peers())
            })
        
        return jsonify(health_info)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """404 에러 핸들러"""
    return jsonify({
        "success": False,
        "message": "요청한 페이지를 찾을 수 없습니다."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logging.error(f"내부 서버 오류: {str(error)}")
    return jsonify({
        "success": False,
        "message": "내부 서버 오류가 발생했습니다."
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """전역 예외 핸들러"""
    logging.error(f"처리되지 않은 예외: {str(e)}")
    return jsonify({
        "success": False,
        "message": f"예상치 못한 오류가 발생했습니다: {str(e)}"
    }), 500

if __name__ == '__main__':
    try:
        # 시작 정보 로깅
        logging.info("=" * 50)
        logging.info("🚀 WireGuard VPN 관리자 시작")
        logging.info("=" * 50)
        
        if wg_manager:
            logging.info(f"📁 설정 파일 경로: {wg_manager.get_config_file_path()}")
            logging.info(f"👥 등록된 피어 수: {len(wg_manager.get_peers())}")
        else:
            logging.warning("⚠️  WireGuard 매니저 초기화 실패")
        
        logging.info("🌐 웹 서버 시작 중...")
        logging.info("📱 브라우저에서 http://localhost:5000 접속")
        logging.info("🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
        logging.info("=" * 50)
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        logging.info("\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        logging.error(f"\n❌ 서버 실행 중 오류 발생: {e}")
        input("엔터를 눌러 종료...")