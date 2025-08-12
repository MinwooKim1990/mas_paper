# 예시: 종합 성능 메트릭 수집 시스템
import time
import statistics
from dataclasses import dataclass
from typing import List, Dict, Any
from collections import defaultdict

@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = None

class SystemMetricsCollector:
    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.current_metrics = {}
        self.measurement_start_time = time.time()
    
    def record_throughput(self, messages_processed: int, time_window: float):
        """처리량 기록 (메시지/초)"""
        throughput = messages_processed / time_window
        metric = PerformanceMetric(
            name="throughput",
            value=throughput,
            unit="messages/second",
            timestamp=time.time(),
            metadata={"messages_count": messages_processed, "time_window": time_window}
        )
        self.metrics_history["throughput"].append(metric)
        self.current_metrics["throughput"] = throughput
    
    def record_latency(self, latency_seconds: float, operation_type: str = "general"):
        """지연시간 기록"""
        metric = PerformanceMetric(
            name="latency",
            value=latency_seconds * 1000,  # 밀리초로 변환
            unit="milliseconds",
            timestamp=time.time(),
            metadata={"operation_type": operation_type}
        )
        self.metrics_history["latency"].append(metric)
    
    def record_resource_usage(self, cpu_percent: float, memory_mb: float, network_mbps: float):
        """리소스 사용량 기록"""
        metrics = [
            PerformanceMetric("cpu_usage", cpu_percent, "percent", time.time()),
            PerformanceMetric("memory_usage", memory_mb, "megabytes", time.time()),
            PerformanceMetric("network_usage", network_mbps, "mbps", time.time())
        ]
        
        for metric in metrics:
            self.metrics_history[metric.name].append(metric)
            self.current_metrics[metric.name] = metric.value
    
    def record_success_rate(self, successful_operations: int, total_operations: int):
        """성공률 기록"""
        success_rate = (successful_operations / total_operations) * 100 if total_operations > 0 else 0
        metric = PerformanceMetric(
            name="success_rate",
            value=success_rate,
            unit="percent",
            timestamp=time.time(),
            metadata={"successful": successful_operations, "total": total_operations}
        )
        self.metrics_history["success_rate"].append(metric)
        self.current_metrics["success_rate"] = success_rate
    def calculate_statistical_summary(self, metric_name: str, time_window_hours: int = 1) -> Dict:
        """메트릭의 통계적 요약"""
        if metric_name not in self.metrics_history:
            return {}
        
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_metrics = [
            m.value for m in self.metrics_history[metric_name]
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            "count": len(recent_metrics),
            "mean": statistics.mean(recent_metrics),
            "median": statistics.median(recent_metrics),
            "std_dev": statistics.stdev(recent_metrics) if len(recent_metrics) > 1 else 0,
            "min": min(recent_metrics),
            "max": max(recent_metrics),
            "percentile_95": self._calculate_percentile(recent_metrics, 95),
            "percentile_99": self._calculate_percentile(recent_metrics, 99)
        }
    
    @staticmethod
    def _calculate_percentile(data: List[float], percentile: int) -> float:
        """백분위수 계산"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_system_health_score(self) -> float:
        """시스템 건강도 점수 (0-100)"""
        scores = []
        
        # 성공률 점수
        if "success_rate" in self.current_metrics:
            scores.append(self.current_metrics["success_rate"])
        
        # CPU 사용률 점수 (80% 이하가 좋음)
        if "cpu_usage" in self.current_metrics:
            cpu_score = max(0, 100 - (self.current_metrics["cpu_usage"] - 80) * 5)
            scores.append(cpu_score)
        
        # 지연시간 점수 (1초 이하가 좋음)
        latency_stats = self.calculate_statistical_summary("latency", 1)
        if latency_stats:
            latency_ms = latency_stats["mean"]
            latency_score = max(0, 100 - (latency_ms / 10))  # 1000ms에서 0점
            scores.append(latency_score)
        
        return statistics.mean(scores) if scores else 0