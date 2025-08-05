# 예시: 스타켈버그 게임 (Stackelberg Game) 구현
import numpy as np
from typing import Dict, List, Tuple, Callable, Any
from dataclasses import dataclass
from scipy.optimize import minimize_scalar, minimize

@dataclass
class StackelbergResult:
    """스타켈버그 게임 결과"""
    leader_strategy: float
    follower_strategy: float
    leader_payoff: float
    follower_payoff: float
    equilibrium_type: str
    market_efficiency: float

class StackelbergGameSolver:
    """스타켈버그 게임 해결사"""
    
    def __init__(self):
        self.game_history = []
        self.market_simulations = []
    
    def solve_stackelberg_game(self, leader_payoff: Callable[[float, float], float],
                             follower_payoff: Callable[[float, float], float],
                             leader_bounds: Tuple[float, float] = (0, 100),
                             follower_bounds: Tuple[float, float] = (0, 100)) -> StackelbergResult:
        """스타켈버그 게임 해결"""
        
        def follower_best_response(leader_strategy: float) -> float:
            """팔로워의 최적 반응 함수"""
            result = minimize_scalar(
                lambda f_strategy: -follower_payoff(leader_strategy, f_strategy),
                bounds=follower_bounds,
                method='bounded'
            )
            return result.x
        
        def leader_objective(leader_strategy: float) -> float:
            """리더의 목적 함수 (팔로워 반응 고려)"""
            follower_response = follower_best_response(leader_strategy)
            return -leader_payoff(leader_strategy, follower_response)
        
        # 리더의 최적 전략 계산
        leader_result = minimize_scalar(
            leader_objective,
            bounds=leader_bounds,
            method='bounded'
        )
        
        optimal_leader_strategy = leader_result.x
        optimal_follower_strategy = follower_best_response(optimal_leader_strategy)
        
        # 균형에서의 보상 계산
        leader_payoff_value = leader_payoff(optimal_leader_strategy, optimal_follower_strategy)
        follower_payoff_value = follower_payoff(optimal_leader_strategy, optimal_follower_strategy)
        
        # 시장 효율성 계산
        market_efficiency = self._calculate_market_efficiency(
            optimal_leader_strategy, optimal_follower_strategy,
            leader_payoff, follower_payoff
        )
        
        return StackelbergResult(
            leader_strategy=optimal_leader_strategy,
            follower_strategy=optimal_follower_strategy,
            leader_payoff=leader_payoff_value,
            follower_payoff=follower_payoff_value,
            equilibrium_type="Stackelberg Equilibrium",
            market_efficiency=market_efficiency
        )
    
    def _calculate_market_efficiency(self, leader_strategy: float, follower_strategy: float,
                                   leader_payoff: Callable, follower_payoff: Callable) -> float:
        """시장 효율성 계산"""
        # 현재 총 이익
        current_total = leader_payoff(leader_strategy, follower_strategy) + \
                       follower_payoff(leader_strategy, follower_strategy)
        
        # 최대 가능한 총 이익 (완전 협력 시)
        def total_payoff(strategies):
            return -(leader_payoff(strategies[0], strategies[1]) + 
                    follower_payoff(strategies[0], strategies[1]))
        
        result = minimize(total_payoff, [leader_strategy, follower_strategy],
                         bounds=[(0, 100), (0, 100)], method='L-BFGS-B')
        
        max_total = -result.fun if result.success else current_total
        
        return current_total / max_total if max_total > 0 else 0.0
    
    def analyze_first_mover_advantage(self, leader_payoff: Callable, follower_payoff: Callable,
                                    simultaneous_payoff: Callable = None) -> Dict[str, Any]:
        """선수 이점 분석"""
        # 스타켈버그 균형
        stackelberg_result = self.solve_stackelberg_game(leader_payoff, follower_payoff)
        
        # 동시 게임 (Nash 균형) 비교를 위한 계산
        if simultaneous_payoff is not None:
            nash_result = self._solve_simultaneous_game(simultaneous_payoff)
        else:
            # 동시 게임을 스타켈버그와 동일한 보상 함수로 가정
            nash_result = self._solve_nash_approximation(leader_payoff, follower_payoff)
        
        # 선수 이점 계산
        first_mover_advantage = stackelberg_result.leader_payoff - nash_result['player1_payoff']
        
        return {
            'stackelberg_equilibrium': stackelberg_result,
            'nash_equilibrium': nash_result,
            'first_mover_advantage': first_mover_advantage,
            'advantage_percentage': (first_mover_advantage / nash_result['player1_payoff'] * 100) 
                                  if nash_result['player1_payoff'] > 0 else 0,
            'market_power_analysis': self._analyze_market_power(stackelberg_result)
        }

    def _solve_nash_approximation(self, payoff1: Callable, payoff2: Callable) -> Dict[str, float]:
        """Nash 균형 근사 계산"""
        def find_best_response_1(strategy2: float) -> float:
            result = minimize_scalar(
                lambda s1: -payoff1(s1, strategy2),
                bounds=(0, 100),
                method='bounded'
            )
            return result.x
        
        def find_best_response_2(strategy1: float) -> float:
            result = minimize_scalar(
                lambda s2: -payoff2(strategy1, s2),
                bounds=(0, 100),
                method='bounded'
            )
            return result.x
        
        # 반복적 최선 반응으로 Nash 균형 찾기
        s1, s2 = 50.0, 50.0  # 초기 추정
        
        for _ in range(50):  # 최대 50번 반복
            new_s1 = find_best_response_1(s2)
            new_s2 = find_best_response_2(s1)
            
            if abs(new_s1 - s1) < 0.01 and abs(new_s2 - s2) < 0.01:
                break
            
            s1, s2 = new_s1, new_s2
        
        return {
            'player1_strategy': s1,
            'player2_strategy': s2,
            'player1_payoff': payoff1(s1, s2),
            'player2_payoff': payoff2(s1, s2)
        }
    
    def _analyze_market_power(self, result: StackelbergResult) -> Dict[str, Any]:
        """시장 지배력 분석"""
        # 리더의 시장 점유율 (전략 값 기준)
        total_output = result.leader_strategy + result.follower_strategy
        leader_market_share = result.leader_strategy / total_output if total_output > 0 else 0
        
        # 수익 점유율
        total_payoff = result.leader_payoff + result.follower_payoff
        leader_payoff_share = result.leader_payoff / total_payoff if total_payoff > 0 else 0
        
        return {
            'leader_market_share': leader_market_share,
            'leader_payoff_share': leader_payoff_share,
            'market_concentration': leader_market_share ** 2 + (1 - leader_market_share) ** 2,  # HHI
            'market_power_index': leader_payoff_share / leader_market_share if leader_market_share > 0 else 0
        }
    
    def simulate_dynamic_stackelberg(self, initial_leader_payoff: Callable, 
                                   initial_follower_payoff: Callable,
                                   periods: int = 10,
                                   learning_rate: float = 0.1) -> Dict[str, Any]:
        """동적 스타켈버그 게임 시뮬레이션"""
        history = []
        
        # 초기 보상 함수
        current_leader_payoff = initial_leader_payoff
        current_follower_payoff = initial_follower_payoff
        
        for period in range(periods):
            # 현재 기간의 균형 계산
            result = self.solve_stackelberg_game(current_leader_payoff, current_follower_payoff)
            
            # 시장 반응 시뮬레이션 (보상 함수 조정)
            def updated_leader_payoff(l_strategy, f_strategy):
                base_payoff = initial_leader_payoff(l_strategy, f_strategy)
                # 경쟁 강도에 따른 수익 감소
                competition_effect = -0.01 * period * (l_strategy + f_strategy)
                return base_payoff + competition_effect
            
            def updated_follower_payoff(l_strategy, f_strategy):
                base_payoff = initial_follower_payoff(l_strategy, f_strategy)
                # 학습 효과로 인한 수익 증가
                learning_effect = 0.005 * period * f_strategy
                return base_payoff + learning_effect
            
            current_leader_payoff = updated_leader_payoff
            current_follower_payoff = updated_follower_payoff
            
            history.append({
                'period': period,
                'result': result,
                'market_conditions': {
                    'competition_intensity': 0.01 * period,
                    'learning_effect': 0.005 * period
                }
            })
        
        return {
            'simulation_history': history,
            'final_equilibrium': history[-1]['result'] if history else None,
            'convergence_analysis': self._analyze_convergence(history),
            'welfare_evolution': self._calculate_welfare_evolution(history)
        }
    
    def _analyze_convergence(self, history: List[Dict]) -> Dict[str, Any]:
        """수렴 분석"""
        if len(history) < 2:
            return {'converged': False, 'reason': 'Insufficient data'}
        
        leader_strategies = [h['result'].leader_strategy for h in history]
        follower_strategies = [h['result'].follower_strategy for h in history]
        
        # 최근 변화율 계산
        recent_leader_change = abs(leader_strategies[-1] - leader_strategies[-2])
        recent_follower_change = abs(follower_strategies[-1] - follower_strategies[-2])
        
        convergence_threshold = 0.1
        converged = (recent_leader_change < convergence_threshold and 
                    recent_follower_change < convergence_threshold)
        
        return {
            'converged': converged,
            'leader_strategy_trend': np.polyfit(range(len(leader_strategies)), leader_strategies, 1)[0],
            'follower_strategy_trend': np.polyfit(range(len(follower_strategies)), follower_strategies, 1)[0],
            'volatility': {
                'leader': np.std(leader_strategies),
                'follower': np.std(follower_strategies)
            }
        }
    
    def _calculate_welfare_evolution(self, history: List[Dict]) -> List[Dict[str, float]]:
        """후생 변화 계산"""
        welfare_data = []
        
        for h in history:
            result = h['result']
            total_welfare = result.leader_payoff + result.follower_payoff
            
            welfare_data.append({
                'period': h['period'],
                'total_welfare': total_welfare,
                'leader_welfare': result.leader_payoff,
                'follower_welfare': result.follower_payoff,
                'efficiency': result.market_efficiency
            })
        
        return welfare_data

# 사용 예시 - 과점 시장
def demonstrate_stackelberg_competition():
    """스타켈버그 경쟁 데모"""
    solver = StackelbergGameSolver()
    
    # 쿠르노 경쟁 형태의 보상 함수
    def leader_profit(q_leader, q_follower):
        """리더의 이익 함수 (수량 경쟁)"""
        price = max(0, 100 - (q_leader + q_follower))  # 선형 수요
        cost = 10  # 한계비용
        return (price - cost) * q_leader
    
    def follower_profit(q_leader, q_follower):
        """팔로워의 이익 함수"""
        price = max(0, 100 - (q_leader + q_follower))
        cost = 15  # 팔로워의 더 높은 한계비용
        return (price - cost) * q_follower
    
    # 스타켈버그 균형 계산
    result = solver.solve_stackelberg_game(leader_profit, follower_profit)
    print(f"Stackelberg Equilibrium: {result}")
    
    # 선수 이점 분석
    advantage_analysis = solver.analyze_first_mover_advantage(leader_profit, follower_profit)
    print(f"First Mover Advantage: {advantage_analysis['first_mover_advantage']:.2f}")
    print(f"Advantage Percentage: {advantage_analysis['advantage_percentage']:.1f}%")
    
    # 동적 시뮬레이션
    dynamic_result = solver.simulate_dynamic_stackelberg(leader_profit, follower_profit, periods=15)
    print(f"Dynamic Simulation Convergence: {dynamic_result['convergence_analysis']['converged']}")