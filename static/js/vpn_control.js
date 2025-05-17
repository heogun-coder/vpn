document.addEventListener('DOMContentLoaded', function() {
    // 요소들 참조
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    const activeTimeElement = document.getElementById('active-time');
    const logsElement = document.getElementById('logs');
    const lastUpdatedElement = document.getElementById('last-updated');
    
    // 상태 추적 변수
    let isConnected = statusIndicator.classList.contains('connected');
    let activeTime = 0;
    let activeTimer = null;
    
    // 상태 업데이트 함수
    function updateStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // 상태 업데이트
                isConnected = data.connected;
                
                // UI 업데이트
                statusIndicator.className = `status-indicator ${isConnected ? 'connected' : 'disconnected'}`;
                statusText.textContent = isConnected ? '연결됨' : '연결되지 않음';
                
                // 버튼 활성화/비활성화
                connectBtn.disabled = isConnected;
                disconnectBtn.disabled = !isConnected;
                
                // 로그 업데이트 (로그 요소가 있는 경우)
                if (logsElement) {
                    const logEntry = document.createElement('p');
                    logEntry.textContent = `[${data.last_updated}] 상태: ${isConnected ? '연결됨' : '연결되지 않음'}`;
                    logsElement.appendChild(logEntry);
                    logsElement.scrollTop = logsElement.scrollHeight;
                }
                
                // 마지막 업데이트 시간 (요소가 있는 경우)
                if (lastUpdatedElement) {
                    lastUpdatedElement.textContent = data.last_updated;
                }
                
                // 활성 타이머 관리
                if (isConnected) {
                    if (!activeTimer) {
                        startActiveTimer();
                    }
                } else {
                    if (activeTimer) {
                        stopActiveTimer();
                    }
                }
            })
            .catch(error => {
                console.error('상태 확인 실패:', error);
                addLog('상태 확인 실패: ' + error.message);
            });
    }
    
    // VPN 연결
    function connectVPN() {
        fetch('/api/connect', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addLog('연결 요청 성공: ' + data.message);
                updateStatus();
            } else {
                addLog('연결 실패: ' + data.message);
            }
        })
        .catch(error => {
            console.error('연결 요청 실패:', error);
            addLog('연결 요청 실패: ' + error.message);
        });
    }
    
    // VPN 연결 해제
    function disconnectVPN() {
        fetch('/api/disconnect', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addLog('연결 해제 요청 성공: ' + data.message);
                updateStatus();
            } else {
                addLog('연결 해제 실패: ' + data.message);
            }
        })
        .catch(error => {
            console.error('연결 해제 요청 실패:', error);
            addLog('연결 해제 요청 실패: ' + error.message);
        });
    }
    
    // 활성 시간 타이머 시작
    function startActiveTimer() {
        activeTime = 0;
        activeTimeElement.textContent = activeTime;
        
        activeTimer = setInterval(() => {
            activeTime++;
            activeTimeElement.textContent = activeTime;
            
            // 5초마다 활성 상태 유지 요청
            if (activeTime % 5 === 0) {
                keepAlive();
            }
        }, 1000);
    }
    
    // 활성 시간 타이머 정지
    function stopActiveTimer() {
        if (activeTimer) {
            clearInterval(activeTimer);
            activeTimer = null;
        }
    }
    
    // 활성 상태 유지
    function keepAlive() {
        if (isConnected) {
            fetch('/api/keep_alive', {
                method: 'POST',
            })
            .then(response => response.json())
            .catch(error => {
                console.error('활성 상태 유지 요청 실패:', error);
            });
        }
    }
    
    // 로그 추가
    function addLog(message) {
        if (logsElement) {
            const logEntry = document.createElement('p');
            const timestamp = new Date().toLocaleTimeString();
            logEntry.textContent = `[${timestamp}] ${message}`;
            logsElement.appendChild(logEntry);
            logsElement.scrollTop = logsElement.scrollHeight;
        }
    }
    
    // 이벤트 리스너 등록
    if (connectBtn) {
        connectBtn.addEventListener('click', connectVPN);
    }
    
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', disconnectVPN);
    }
    
    // 탭 활성화/비활성화 감지
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            // 탭이 활성화될 때 상태 업데이트 및 활성 유지
            updateStatus();
            if (isConnected) {
                keepAlive();
            }
        }
    });
    
    // 페이지 새로고침 시 연결 유지를 위한 이벤트
    window.addEventListener('beforeunload', function() {
        if (isConnected) {
            keepAlive();
        }
    });
    
    // 초기 상태 조회
    updateStatus();
    
    // 주기적 상태 업데이트 (10초마다)
    setInterval(updateStatus, 10000);
});