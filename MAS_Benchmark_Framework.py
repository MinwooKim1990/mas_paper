# 예시: MAS 벤치마킹 프레임워크
import asyncio
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Any

class BenchmarkScenario(ABC):
    """벤치마크 시나리오 기본 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.results = {}
    
    @abstractmethod
    async def setup(self, agents: List[Any]) -> None:
        """벤치마크 환경 설정"""
        pass
    
    @abstractmethod
    async def run(self, duration_seconds: int) -> Dict[str, Any]:
        """벤치마크 실행"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """정리 작업"""
        pass

class MessagePassingBenchmark(BenchmarkScenario):
    """메시지 패싱 성능 벤치마크"""
    
    def __init__(self):
        super().__init__(
            "Message Passing Performance",
            "Tests message throughput and latency between agents"
        )
        self.agents = []
        self.message_count = 0
        self.latency_measurements = []
    
    async def setup(self, agents: List[Any]) -> None:
        self.agents = agents
        self.message_count = 0
        self.latency_measurements = []
    
    async def run(self, duration_seconds: int) -> Dict[str, Any]:
        start_time = time.time()
        tasks = []
        
        # 각 에이전트 쌍 간 메시지 교환 작업 생성
        for i in range(len(self.agents)):
            for j in range(len(self.agents)):
                if i != j:
                    task = asyncio.create_task(
                        self._message_exchange_test(self.agents[i], self.agents[j], duration_seconds)
                    )
                    tasks.append(task)
        
        # 모든 작업 완료 대기
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        return {
            'total_messages': self.message_count,
            'messages_per_second': self.message_count / total_time,
            'average_latency_ms': statistics.mean(self.latency_measurements) if self.latency_measurements else 0,
            'max_latency_ms': max(self.latency_measurements) if self.latency_measurements else 0,
            'min_latency_ms': min(self.latency_measurements) if self.latency_measurements else 0,
            'total_duration': total_time
        }
    
    async def _message_exchange_test(self, sender, receiver, duration: int):
        """두 에이전트 간 메시지 교환 테스트"""
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # 메시지 전송 시간 측정
            send_start = time.time()
            
            # 간단한 ping 메시지 전송
            message = {
                'type': 'ping',
                'timestamp': send_start,
                'sender_id': sender.agent_id
            }
            
            # 실제 메시지 전송 (에이전트 구현에 따라 다름)
            response = await self._send_message(sender, receiver, message)
            
            if response:
                latency = (time.time() - send_start) * 1000  # 밀리초
                self.latency_measurements.append(latency)
                self.message_count += 1
            
            # 짧은 대기 (과부하 방지)
            await asyncio.sleep(0.01)
    
    async def _send_message(self, sender, receiver, message):
        """실제 메시지 전송 (구현체에 따라 다름)"""
        try:
            # 에이전트의 메시지 전송 메서드 호출
            return await sender.send_message(receiver.agent_id, message)
        except Exception:
            return None
    
    async def cleanup(self) -> None:
        self.agents = []
        self.message_count = 0
        self.latency_measurements = []
class ScalabilityBenchmark(BenchmarkScenario):
    """확장성 벤치마크"""
    
    def __init__(self):
        super().__init__(
            "Scalability Test",
            "Tests system performance with increasing number of agents"
        )
        self.performance_data = []
    
    async def setup(self, agents: List[Any]) -> None:
        self.performance_data = []
    
    async def run(self, duration_seconds: int) -> Dict[str, Any]:
        """다양한 에이전트 수로 성능 테스트"""
        agent_counts = [5, 10, 25, 50, 100, 200]
        results = {}
        
        for count in agent_counts:
            if count <= len(self.agents):
                print(f"Testing with {count} agents...")
                
                # 지정된 수의 에이전트만 사용
                test_agents = self.agents[:count]
                
                # 메시지 패싱 벤치마크 실행
                benchmark = MessagePassingBenchmark()
                await benchmark.setup(test_agents)
                result = await benchmark.run(duration_seconds // len(agent_counts))
                
                results[f"{count}_agents"] = result
                self.performance_data.append({
                    'agent_count': count,
                    'throughput': result['messages_per_second'],
                    'latency': result['average_latency_ms']
                })
        
        # 확장성 분석
        scalability_analysis = self._analyze_scalability()
        
        return {
            'performance_by_agent_count': results,
            'scalability_analysis': scalability_analysis
        }
    
    def _analyze_scalability(self) -> Dict[str, Any]:
        """확장성 분석"""
        if len(self.performance_data) < 2:
            return {}
        
        # 처리량 변화율 계산
        throughput_ratios = []
        latency_ratios = []
        
        for i in range(1, len(self.performance_data)):
            prev = self.performance_data[i-1]
            curr = self.performance_data[i]
            
            throughput_ratio = curr['throughput'] / prev['throughput']
            latency_ratio = curr['latency'] / prev['latency']
            
            throughput_ratios.append(throughput_ratio)
            latency_ratios.append(latency_ratio)
        
        return {
            'avg_throughput_ratio': statistics.mean(throughput_ratios),
            'avg_latency_ratio': statistics.mean(latency_ratios),
            'linear_scalability_score': self._calculate_linearity_score(throughput_ratios),
            'performance_degradation': max(latency_ratios) if latency_ratios else 1.0
        }
    
    def _calculate_linearity_score(self, ratios: List[float]) -> float:
        """선형 확장성 점수 계산 (1.0에 가까울수록 이상적)"""
        if not ratios:
            return 0.0
        
        # 이상적 비율은 1.0 (선형 확장)
        deviations = [abs(ratio - 1.0) for ratio in ratios]
        avg_deviation = statistics.mean(deviations)
        
        # 0-1 점수로 변환 (낮은 편차가 높은 점수)
        return max(0.0, 1.0 - avg_deviation)
    
    async def cleanup(self) -> None:
        self.performance_data = []
class CoordinationBenchmark(BenchmarkScenario):
    """협업/조정 성능 벤치마크"""
    
    def __init__(self):
        super().__init__(
            "Coordination Performance",
            "Tests agent coordination and consensus-reaching capabilities"
        )
        self.coordination_tasks = []
        self.consensus_times = []
    
    async def setup(self, agents: List[Any]) -> None:
        self.coordination_tasks = []
        self.consensus_times = []
    
    async def run(self, duration_seconds: int) -> Dict[str, Any]:
        """협업 작업 벤치마크 실행"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        task_id = 0
        while time.time() < end_time:
            # 협업 작업 생성
            task = {
                'task_id': task_id,
                'type': 'consensus',
                'target_value': random.randint(1, 100),
                'participants': random.sample(self.agents, min(5, len(self.agents)))
            }
            
            # 합의 도달 시간 측정
            consensus_start = time.time()
            consensus_reached = await self._run_consensus_task(task)
            consensus_time = time.time() - consensus_start
            
            if consensus_reached:
                self.consensus_times.append(consensus_time)
                self.coordination_tasks.append(task)
            
            task_id += 1
            await asyncio.sleep(0.1)  # 작업 간 간격
        
        return {
            'total_coordination_tasks': len(self.coordination_tasks),
            'successful_consensus_rate': len(self.consensus_times) / max(task_id, 1) * 100,
            'average_consensus_time': statistics.mean(self.consensus_times) if self.consensus_times else 0,
            'coordination_efficiency': self._calculate_coordination_efficiency()
        }
    
    async def _run_consensus_task(self, task: Dict) -> bool:
        """합의 작업 실행"""
        try:
            # 간단한 평균 기반 합의 시뮬레이션
            values = []
            for agent in task['participants']:
                # 각 에이전트가 제안하는 값
                proposed_value = random.randint(
                    max(1, task['target_value'] - 10),
                    task['target_value'] + 10
                )
                values.append(proposed_value)
            
            # 평균값으로 합의
            consensus_value = statistics.mean(values)
            
            # 목표값과의 차이가 5 이하면 성공
            return abs(consensus_value - task['target_value']) <= 5
            
        except Exception:
            return False
    
    def _calculate_coordination_efficiency(self) -> float:
        """협업 효율성 계산"""
        if not self.consensus_times:
            return 0.0
        
        # 빠른 합의일수록 높은 효율성
        avg_time = statistics.mean(self.consensus_times)
        max_acceptable_time = 5.0  # 5초
        
        efficiency = max(0.0, (max_acceptable_time - avg_time) / max_acceptable_time)
        return efficiency * 100
    
    async def cleanup(self) -> None:
        self.coordination_tasks = []
        self.consensus_times = []

class BenchmarkRunner:
    """벤치마크 실행 관리자"""
    
    def __init__(self):
        self.benchmarks = {}
        self.results_history = []
    
    def register_benchmark(self, benchmark: BenchmarkScenario):
        """벤치마크 등록"""
        self.benchmarks[benchmark.name] = benchmark
    
    async def run_all_benchmarks(self, agents: List[Any], duration_per_test: int = 60) -> Dict[str, Any]:
        """모든 등록된 벤치마크 실행"""
        all_results = {}
        
        for name, benchmark in self.benchmarks.items():
            print(f"Running benchmark: {name}")
            
            try:
                await benchmark.setup(agents)
                result = await benchmark.run(duration_per_test)
                await benchmark.cleanup()
                
                all_results[name] = {
                    'status': 'completed',
                    'results': result,
                    'timestamp': time.time()
                }
                
            except Exception as e:
                all_results[name] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        # 결과 히스토리에 저장
        self.results_history.append({
            'timestamp': time.time(),
            'agent_count': len(agents),
            'results': all_results
        })
        
        return all_results
    
    def generate_benchmark_report(self, results: Dict[str, Any]) -> str:
        """벤치마크 보고서 생성"""
        report = []
        report.append("=" * 50)
        report.append("Multi-Agent System Benchmark Report")
        report.append("=" * 50)
        report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for benchmark_name, result in results.items():
            report.append(f"Benchmark: {benchmark_name}")
            report.append("-" * 30)
            
            if result['status'] == 'completed':
                benchmark_results = result['results']
                
                if benchmark_name == "Message Passing Performance":
                    report.append(f"  Messages per second: {benchmark_results.get('messages_per_second', 0):.2f}")
                    report.append(f"  Average latency: {benchmark_results.get('average_latency_ms', 0):.2f} ms")
                    report.append(f"  Total messages: {benchmark_results.get('total_messages', 0)}")
                
                elif benchmark_name == "Scalability Test":
                    analysis = benchmark_results.get('scalability_analysis', {})
                    report.append(f"  Linear scalability score: {analysis.get('linear_scalability_score', 0):.2f}")
                    report.append(f"  Performance degradation: {analysis.get('performance_degradation', 0):.2f}x")
                
                elif benchmark_name == "Coordination Performance":
                    report.append(f"  Consensus success rate: {benchmark_results.get('successful_consensus_rate', 0):.1f}%")
                    report.append(f"  Average consensus time: {benchmark_results.get('average_consensus_time', 0):.2f}s")
                    report.append(f"  Coordination efficiency: {benchmark_results.get('coordination_efficiency', 0):.1f}%")
            
            else:
                report.append(f"  Status: FAILED")
                report.append(f"  Error: {result.get('error', 'Unknown error')}")
            
            report.append("")
        
        return "\n".join(report)
    
    def compare_benchmark_results(self, current_results: Dict, baseline_results: Dict) -> Dict[str, Any]:
        """벤치마크 결과 비교"""
        comparison = {}
        
        for benchmark_name in current_results.keys():
            if benchmark_name in baseline_results:
                current = current_results[benchmark_name].get('results', {})
                baseline = baseline_results[benchmark_name].get('results', {})
                
                comparison[benchmark_name] = self._compare_metrics(current, baseline)
        
        return comparison
    
    def _compare_metrics(self, current: Dict, baseline: Dict) -> Dict[str, float]:
        """메트릭 비교"""
        comparison = {}
        
        common_metrics = set(current.keys()) & set(baseline.keys())
        
        for metric in common_metrics:
            if isinstance(current[metric], (int, float)) and isinstance(baseline[metric], (int, float)):
                if baseline[metric] != 0:
                    improvement = ((current[metric] - baseline[metric]) / baseline[metric]) * 100
                    comparison[metric] = improvement
                else:
                    comparison[metric] = 0.0
        
        return comparison