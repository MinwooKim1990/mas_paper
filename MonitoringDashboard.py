# 예시: 실시간 모니터링 대시보드
import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import websockets


class RealTimeMonitor:
    def __init__(self):
        self.connected_clients = set()
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'response_time': 2000.0,
        }
        self.active_alerts: Dict[str, Dict[str, Any]] = {}

    async def start_monitoring(self, agents: List[Any]):
        monitoring_tasks = [
            asyncio.create_task(self._monitor_agent(agent))
            for agent in agents
        ]
        monitoring_tasks.append(asyncio.create_task(self._broadcast_metrics()))
        await asyncio.gather(*monitoring_tasks)

    async def _monitor_agent(self, agent):
        while True:
            try:
                metrics = await self._collect_agent_metrics(agent)
                entry = {
                    'timestamp': datetime.now().isoformat(),
                    'agent_id': agent.agent_id,
                    'metrics': metrics,
                }
                self.metrics_buffer.append(entry)
                await self._check_alerts(agent.agent_id, metrics)
                if len(self.metrics_buffer) > 1000:
                    self.metrics_buffer = self.metrics_buffer[-500:]
            except Exception as exc:
                print(f"Error monitoring agent {agent.agent_id}: {exc}")
            await asyncio.sleep(5)

    async def _collect_agent_metrics(self, agent) -> Dict[str, float]:
        return {
            'cpu_usage': random.uniform(20, 90),
            'memory_usage': random.uniform(30, 80),
            'active_tasks': random.randint(0, 10),
            'messages_per_minute': random.randint(10, 100),
            'error_rate': random.uniform(0, 10),
            'response_time': random.uniform(100, 1500),
        }

    async def _check_alerts(self, agent_id: str, metrics: Dict[str, float]):
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name not in metrics:
                continue
            value = metrics[metric_name]
            key = f"{agent_id}_{metric_name}"
            if value > threshold:
                if key not in self.active_alerts:
                    alert = {
                        'agent_id': agent_id,
                        'metric': metric_name,
                        'value': value,
                        'threshold': threshold,
                        'severity': self._determine_severity(value, threshold),
                        'timestamp': datetime.now().isoformat(),
                    }
                    self.active_alerts[key] = alert
                    await self._send_alert(alert)
            elif key in self.active_alerts:
                resolved = self.active_alerts.pop(key)
                resolved['status'] = 'resolved'
                resolved['resolved_at'] = datetime.now().isoformat()
                await self._send_alert(resolved)

    def _determine_severity(self, value: float, threshold: float) -> str:
        ratio = value / threshold
        if ratio >= 1.5:
            return 'critical'
        if ratio >= 1.2:
            return 'high'
        if ratio >= 1.0:
            return 'warning'
        return 'normal'

    async def _send_alert(self, alert: Dict[str, Any]):
        message = {'type': 'alert', 'data': alert}
        await self._broadcast_to_clients(message)

    async def _broadcast_metrics(self):
        while True:
            if self.metrics_buffer:
                await self._broadcast_to_clients({
                    'type': 'metrics',
                    'data': self.metrics_buffer[-1],
                })
            await asyncio.sleep(2)

    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        if not self.connected_clients:
            return
        message_json = json.dumps(message)
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except Exception:
                disconnected.add(client)
        self.connected_clients -= disconnected

    def add_client(self, websocket_client):
        self.connected_clients.add(websocket_client)

    def remove_client(self, websocket_client):
        self.connected_clients.discard(websocket_client)

    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            entry for entry in self.metrics_buffer
            if datetime.fromisoformat(entry['timestamp']) >= cutoff
        ]

    def export_metrics(self, format_type: str = 'json') -> str:
        if format_type == 'json':
            return json.dumps(self.metrics_buffer, indent=2)
        if format_type == 'csv':
            return self._convert_to_csv()
        raise ValueError(f"Unsupported format: {format_type}")

    def _convert_to_csv(self) -> str:
        if not self.metrics_buffer:
            return ''
        headers = ['timestamp', 'agent_id'] + list(self.metrics_buffer[0]['metrics'].keys())
        lines = [','.join(headers)]
        for entry in self.metrics_buffer:
            row = [
                entry['timestamp'],
                entry['agent_id'],
                *[str(entry['metrics'].get(h, '')) for h in headers[2:]],
            ]
            lines.append(','.join(row))
        return '\n'.join(lines)

    def _calculate_system_health(self, cpu: float, memory: float, errors: float) -> str:
        score = 100
        if cpu > 80:
            score -= (cpu - 80) * 2
        if memory > 80:
            score -= (memory - 80) * 2
        score -= errors * 5
        if score >= 90:
            return 'excellent'
        if score >= 75:
            return 'good'
        if score >= 60:
            return 'fair'
        if score >= 40:
            return 'poor'
        return 'critical'

    def _calculate_system_summary(self) -> Dict[str, Any]:
        if not self.metrics_buffer:
            return {}
        latest = self.metrics_buffer[-1]['metrics']
        health = self._calculate_system_health(
            latest.get('cpu_usage', 0),
            latest.get('memory_usage', 0),
            latest.get('error_rate', 0),
        )
        return {
            'latest_metrics': latest,
            'system_health': health,
        }


class MonitoringWebServer:
    """모니터링 웹 서버"""

    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor

    async def websocket_handler(self, websocket, path):
        self.monitor.add_client(websocket)
        try:
            initial = {
                'type': 'initial_data',
                'data': self.monitor.get_historical_data(1),
                'summary': self.monitor._calculate_system_summary(),
            }
            await websocket.send(json.dumps(initial))
            async for message in websocket:
                try:
                    request = json.loads(message)
                    await self._handle_client_request(websocket, request)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.monitor.remove_client(websocket)

    async def _handle_client_request(self, websocket, request: Dict[str, Any]):
        req_type = request.get('type')
        if req_type == 'get_historical_data':
            hours = request.get('hours', 24)
            data = self.monitor.get_historical_data(hours)
            await websocket.send(json.dumps({'type': 'historical_data', 'data': data}))
        elif req_type == 'export_metrics':
            fmt = request.get('format', 'json')
            exported = self.monitor.export_metrics(fmt)
            await websocket.send(json.dumps({'type': 'exported_data', 'format': fmt, 'data': exported}))

