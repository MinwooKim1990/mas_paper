# 예시: 실시간 모니터링 대시보드
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import websocket
from dataclasses import asdict

class RealTimeMonitor:
    def __init__(self):
        self.connected_clients = set()
        self.metrics_buffer = []
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'response_time': 2000.0  # 2초
        }
        self.active_alerts = {}
    
    async def start_monitoring(self, agents: List[Any]):
        """모니터링 시작"""
        monitoring_tasks = []
        
        for agent in agents:
            task = asyncio.create_task(self._monitor_agent(agent))
            monitoring_tasks.append(task)
        
        # 메트릭 브로드캐스트 태스크
        broadcast_task = asyncio.create_task(self._broadcast_metrics())
        monitoring_tasks.append(broadcast_task)
        
        await asyncio.gather(*monitoring_tasks)
    
    async def _monitor_agent(self, agent):
        """개별 에이전트 모니터링"""
        while True:
            try:
                # 에이전트 메트릭 수집
                metrics = await self._collect_agent_metrics(agent)
                
                # 메트릭 버퍼에 추가
                self.metrics_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    'agent_id': agent.agent_id,
                    'metrics': metrics
                })
                
                # 알림 확인
                await self._check_alerts(agent.agent_id, metrics)
                
                # 버퍼 크기 제한
                if len(self.metrics_buffer) > 1000:
                    self.metrics_buffer = self.metrics_buffer[-500:]
                
            except Exception as e:
                print(f"Error monitoring agent {agent.agent_id}: {e}")
            
            await asyncio.sleep(5)  # 5초 간격으로 모니터링
    
    async def _collect_agent_metrics(self, agent) -> Dict[str, float]:
        """에이전트 메트릭 수집"""
        # 실제 구현에서는 에이전트의 메트릭 API 호출
        return {
            'cpu_usage': random.uniform(20, 90),
            'memory_usage': random.uniform(30, 80),
            'active_tasks': random.randint(0, 10),
            'messages_per_minute': random.randint(10, 100),
            'error_count': random.randint(0, 5),
            'response_time': random.uniform(100, 1500)
        }
    
    async def _check_alerts(self, agent_id: str, metrics: Dict[str, float]):
        """알림 조건 확인"""
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name in metrics:
                current_value = metrics[metric_name]
                alert_key = f"{agent_id}_{metric_name}"
                
                # 임계값 초과 시 알림
                if current_value > threshold:
                    if alert_key not in self.active_alerts:
                        alert = {
                            'agent_id': agent_id,
                            'metric': metric_name,
                            'value': current_value,
                            'threshold': threshold,
                            'severity': self._determine_severity(current_value, threshold),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.active_alerts[alert_key] = alert
                        await self._send_alert(alert)
                
                # 정상 범위로 돌아온 경우 알림 해제
                elif alert_key in self.active_alerts:
                    resolved_alert = self.active_alerts.pop(alert_key)
                    resolved_alert['status'] = 'resolved'
                    resolved_alert['resolved_at'] = datetime.now().isoformat()
                    await self._send_alert(resolved_alert)

# 예시: 실시간 모니터링 대시보드
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import websocket
from dataclasses import asdict

class RealTimeMonitor:
    def __init__(self):
        self.connected_clients = set()
        self.metrics_buffer = []
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'response_time': 2000.0  # 2초
        }
        self.active_alerts = {}
    
    async def start_monitoring(self, agents: List[Any]):
        """모니터링 시작"""
        monitoring_tasks = []
        
        for agent in agents:
            task = asyncio.create_task(self._monitor_agent(agent))
            monitoring_tasks.append(task)
        
        # 메트릭 브로드캐스트 태스크
        broadcast_task = asyncio.create_task(self._broadcast_metrics())
        monitoring_tasks.append(broadcast_task)
        
        await asyncio.gather(*monitoring_tasks)
    
    async def _monitor_agent(self, agent):
        """개별 에이전트 모니터링"""
        while True:
            try:
                # 에이전트 메트릭 수집
                metrics = await self._collect_agent_metrics(agent)
                
                # 메트릭 버퍼에 추가
                self.metrics_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    'agent_id': agent.agent_id,
                    'metrics': metrics
                })
                
                # 알림 확인
                await self._check_alerts(agent.agent_id, metrics)
                
                # 버퍼 크기 제한
                if len(self.metrics_buffer) > 1000:
                    self.metrics_buffer = self.metrics_buffer[-500:]
                
            except Exception as e:
                print(f"Error monitoring agent {agent.agent_id}: {e}")
            
            await asyncio.sleep(5)  # 5초 간격으로 모니터링
    
    async def _collect_agent_metrics(self, agent) -> Dict[str, float]:
        """에이전트 메트릭 수집"""
        # 실제 구현에서는 에이전트의 메트릭 API 호출
        return {
            'cpu_usage': random.uniform(20, 90),
            'memory_usage': random.uniform(30, 80),
            'active_tasks': random.randint(0, 10),
            'messages_per_minute': random.randint(10, 100),
            'error_count': random.randint(0, 5),
            'response_time': random.uniform(100, 1500)
        }
    
    async def _check_alerts(self, agent_id: str, metrics: Dict[str, float]):
        """알림 조건 확인"""
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name in metrics:
                current_value = metrics[metric_name]
                alert_key = f"{agent_id}_{metric_name}"
                
                # 임계값 초과 시 알림
                if current_value > threshold:
                    if alert_key not in self.active_alerts:
                        alert = {
                            'agent_id': agent_id,
                            'metric': metric_name,
                            'value': current_value,
                            'threshold': threshold,
                            'severity': self._determine_severity(current_value, threshold),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.active_alerts[alert_key] = alert
                        await self._send_alert(alert)
                
                # 정상 범위로 돌아온 경우 알림 해제
                elif alert_key in self.active_alerts:
                    resolved_alert = self.active_alerts.pop(alert_key)
                    resolved_alert['status'] = 'resolved'
                    resolved_alert['resolved_at'] = datetime.now().isoformat()
                    await self._send_alert(resolved_alert)

    def _calculate_system_health(self, cpu: float, memory: float, errors: int) -> str:
        """시스템 건강도 계산"""
        score = 100
        
        # CPU 사용률 페널티
        if cpu > 80:
            score -= (cpu - 80) * 2
        
        # 메모리 사용률 페널티
        if memory > 80:
            score -= (memory - 80) * 2
        
        # 오류 페널티
        score -= errors * 5
        
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
    
    async def _broadcast_to_clients(self, message: Dict):
        """연결된 클라이언트들에게 메시지 브로드캐스트"""
        if not self.connected_clients:
            return
        
        message_json = json.dumps(message)
        
        # 연결이 끊어진 클라이언트 제거
        disconnected_clients = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except Exception:
                disconnected_clients.add(client)
        
        self.connected_clients -= disconnected_clients
    
    def add_client(self, websocket_client):
        """새 클라이언트 연결"""
        self.connected_clients.add(websocket_client)
    
    def remove_client(self, websocket_client):
        """클라이언트 연결 해제"""
        self.connected_clients.discard(websocket_client)
    
    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        """과거 데이터 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            entry for entry in self.metrics_buffer
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """메트릭 데이터 내보내기"""
        if format_type == 'json':
            return json.dumps(self.metrics_buffer, indent=2)
        elif format_type == 'csv':
            return self._convert_to_csv()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _convert_to_csv(self) -> str:
        """CSV 형식으로 변환"""
        if not self.metrics_buffer:
            return ""
        
        # CSV 헤더
        headers = ['timestamp', 'agent_id']
        if self.metrics_buffer:
            sample_metrics = self.metrics_buffer[0]['metrics']
            headers.extend(sample_metrics.keys())
        
        csv_lines = [','.join(headers)]
        
        # 데이터 행
        for entry in self.metrics_buffer:
            row = [entry['timestamp'], entry['agent_id']]
            metrics = entry['metrics']
            row.extend(str(metrics.get(header, '')) for header in headers[2:])
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)
    
class MonitoringWebServer:
    """모니터링 웹 서버"""
    
    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor
    
    async def websocket_handler(self, websocket, path):
        """WebSocket 연결 처리"""
        self.monitor.add_client(websocket)
        
        try:
            # 초기 데이터 전송
            initial_data = {
                'type': 'initial_data',
                'data': self.monitor.get_historical_data(1),  # 최근 1시간
                'summary': self.monitor._calculate_system_summary()
            }
            await websocket.send(json.dumps(initial_data))
            
            # 연결 유지
            async for message in websocket:
                # 클라이언트로부터의 요청 처리
                try:
                    request = json.loads(message)
                    await self._handle_client_request(websocket, request)
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.monitor.remove_client(websocket)
    
    async def _handle_client_request(self, websocket, request: Dict):
        """클라이언트 요청 처리"""
        request_type = request.get('type')
        
        if request_type == 'get_historical_data':
            hours = request.get('hours', 24)
            data = self.monitor.get_historical_data(hours)
            response = {
                'type': 'historical_data',
                'data': data
            }
            await websocket.send(json.dumps(response))
        
        elif request_type == 'export_metrics':
            format_type = request.get('format', 'json')
            exported_data = self.monitor.export_metrics(format_type)
            response = {
                'type': 'exported_data',
                'format': format_type,
                'data': exported_data
            }
            await websocket.send(json.dumps(response))