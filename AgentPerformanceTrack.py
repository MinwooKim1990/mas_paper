# 예시: 개별 에이전트 성능 추적
import time
import statistics
from collections import defaultdict
from typing import Any, Dict, List


class AgentPerformanceTracker:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.task_history = []
        self.communication_stats = defaultdict(int)
        self.error_log = []
        self.start_time = time.time()
    
    def record_task_completion(self, task_id: str, duration: float, success: bool, complexity: int = 1):
        """작업 완료 기록"""
        task_record = {
            'task_id': task_id,
            'duration': duration,
            'success': success,
            'complexity': complexity,
            'timestamp': time.time()
        }
        self.task_history.append(task_record)
    
    def record_communication(self, message_type: str, direction: str, size_bytes: int):
        """통신 기록"""
        self.communication_stats[f"{direction}_{message_type}"] += 1
        self.communication_stats[f"{direction}_bytes"] += size_bytes
    
    def record_error(self, error_type: str, error_message: str, severity: str):
        """오류 기록"""
        error_record = {
            'error_type': error_type,
            'message': error_message,
            'severity': severity,
            'timestamp': time.time()
        }
        self.error_log.append(error_record)
    
    def get_task_completion_rate(self, time_window_hours: int = 24) -> float:
        """작업 완료율"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_tasks = [t for t in self.task_history if t['timestamp'] >= cutoff_time]
        
        if not recent_tasks:
            return 0.0
        
        successful_tasks = sum(1 for t in recent_tasks if t['success'])
        return (successful_tasks / len(recent_tasks)) * 100
    
    def get_average_task_duration(self, time_window_hours: int = 24) -> float:
        """평균 작업 수행 시간"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_tasks = [t for t in self.task_history if t['timestamp'] >= cutoff_time and t['success']]
        
        if not recent_tasks:
            return 0.0
        
        return statistics.mean(t['duration'] for t in recent_tasks)
    
    def get_throughput(self, time_window_hours: int = 1) -> float:
        """작업 처리량 (작업/시간)"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_tasks = [t for t in self.task_history if t['timestamp'] >= cutoff_time]
        
        return len(recent_tasks) / time_window_hours
    
    def get_communication_efficiency(self) -> Dict[str, float]:
        """통신 효율성 지표"""
        total_sent = self.communication_stats.get('sent_bytes', 0)
        total_received = self.communication_stats.get('received_bytes', 0)
        sent_messages = self.communication_stats.get('sent_message', 0)
        received_messages = self.communication_stats.get('received_message', 0)
        
        return {
            'avg_message_size_sent': total_sent / max(sent_messages, 1),
            'avg_message_size_received': total_received / max(received_messages, 1),
            'total_bandwidth_used': total_sent + total_received,
            'message_exchange_ratio': sent_messages / max(received_messages, 1)
        }
    
    def get_error_rate(self, time_window_hours: int = 24) -> Dict[str, float]:
        """오류율 분석"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_errors = [e for e in self.error_log if e['timestamp'] >= cutoff_time]
        
        if not recent_errors:
            return {'total_error_rate': 0.0, 'critical_error_rate': 0.0}
        
        total_operations = len(self.task_history)
        critical_errors = sum(1 for e in recent_errors if e['severity'] == 'critical')
        
        return {
            'total_error_rate': (len(recent_errors) / max(total_operations, 1)) * 100,
            'critical_error_rate': (critical_errors / max(total_operations, 1)) * 100,
            'errors_by_type': self._group_errors_by_type(recent_errors)
        }
    
    def _group_errors_by_type(self, errors: List[Dict]) -> Dict[str, int]:
        """오류 유형별 그룹화"""
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error['error_type']] += 1
        return dict(error_counts)
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """종합 성능 보고서 생성"""
        uptime = time.time() - self.start_time
        
        return {
            'agent_id': self.agent_id,
            'uptime_hours': uptime / 3600,
            'task_completion_rate': self.get_task_completion_rate(),
            'average_task_duration': self.get_average_task_duration(),
            'throughput_per_hour': self.get_throughput(),
            'communication_efficiency': self.get_communication_efficiency(),
            'error_analysis': self.get_error_rate(),
            'total_tasks_completed': len([t for t in self.task_history if t['success']]),
            'total_tasks_attempted': len(self.task_history)
        }
