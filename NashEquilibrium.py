# 예시: 내쉬 균형 (Nash Equilibrium) 구현
import numpy as np
from typing import List, Tuple, Dict, Any
from itertools import product

class NashEquilibriumSolver:
    """내쉬 균형 계산 및 분석"""
    
    def __init__(self):
        self.games_history = []
        self.equilibria_found = []
    
    def find_pure_strategy_nash(self, payoff_matrices: List[np.ndarray]) -> List[Tuple]:
        """순수 전략 내쉬 균형 찾기"""
        if len(payoff_matrices) != 2:
            raise ValueError("Currently supports only 2-player games")
        
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        m, n = player1_payoffs.shape
        nash_equilibria = []
        
        # 모든 전략 조합 확인
        for i in range(m):
            for j in range(n):
                is_nash = True
                
                # Player 1의 최적 반응 확인
                player1_current = player1_payoffs[i, j]
                for k in range(m):
                    if k != i and player1_payoffs[k, j] > player1_current:
                        is_nash = False
                        break
                
                if not is_nash:
                    continue
                
                # Player 2의 최적 반응 확인
                player2_current = player2_payoffs[i, j]
                for l in range(n):
                    if l != j and player2_payoffs[i, l] > player2_current:
                        is_nash = False
                        break
                
                if is_nash:
                    nash_equilibria.append((i, j))
        
        return nash_equilibria
    
    def calculate_mixed_strategy_nash(self, payoff_matrices: List[np.ndarray]) -> Dict[str, Any]:
        """혼합 전략 내쉬 균형 계산"""
        from scipy.optimize import linprog
        
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        m, n = player1_payoffs.shape
        
        # Player 1의 혼합 전략 계산
        # Player 2가 각 전략을 사용할 확률을 q라 할 때,
        # Player 1의 각 순수 전략의 기댓값이 같아야 함
        
        if n > 1:
            # Player 2의 무차별 조건 설정
            A_eq = []
            b_eq = []
            
            for i in range(m - 1):
                row = []
                for j in range(n):
                    row.append(player1_payoffs[i, j] - player1_payoffs[i + 1, j])
                A_eq.append(row)
                b_eq.append(0)
            
            # 확률 합이 1이어야 함
            A_eq.append([1] * n)
            b_eq.append(1)
            
            # 모든 확률이 0 이상이어야 함
            bounds = [(0, 1) for _ in range(n)]
            
            try:
                result = linprog(
                    c=[0] * n,  # 목적함수 (무관)
                    A_eq=A_eq,
                    b_eq=b_eq,
                    bounds=bounds,
                    method='highs'
                )
                
                if result.success:
                    player2_mixed = result.x
                    
                    # Player 1의 혼합 전략도 유사하게 계산
                    player1_mixed = self._calculate_player1_mixed(
                        player2_payoffs.T, player2_mixed
                    )
                    
                    return {
                        'player1_strategy': player1_mixed,
                        'player2_strategy': player2_mixed,
                        'expected_payoffs': self._calculate_expected_payoffs(
                            payoff_matrices, player1_mixed, player2_mixed
                        )
                    }
            except:
                pass
        
        return {'status': 'No mixed strategy equilibrium found'}

    def _calculate_player1_mixed(self, transposed_payoffs: np.ndarray, 
                                opponent_strategy: np.ndarray) -> np.ndarray:
        """Player 1의 혼합 전략 계산"""
        from scipy.optimize import linprog
        
        n, m = transposed_payoffs.shape
        
        if m > 1:
            A_eq = []
            b_eq = []
            
            for j in range(n - 1):
                row = []
                for i in range(m):
                    row.append(transposed_payoffs[j, i] - transposed_payoffs[j + 1, i])
                A_eq.append(row)
                b_eq.append(0)
            
            A_eq.append([1] * m)
            b_eq.append(1)
            
            bounds = [(0, 1) for _ in range(m)]
            
            try:
                result = linprog(
                    c=[0] * m,
                    A_eq=A_eq,
                    b_eq=b_eq,
                    bounds=bounds,
                    method='highs'
                )
                
                if result.success:
                    return result.x
            except:
                pass
        
        # 기본값: 균등 분포
        return np.ones(m) / m
    
    def _calculate_expected_payoffs(self, payoff_matrices: List[np.ndarray],
                                  strategy1: np.ndarray, strategy2: np.ndarray) -> Tuple[float, float]:
        """기댓값 계산"""
        payoff1 = np.sum(payoff_matrices[0] * np.outer(strategy1, strategy2))
        payoff2 = np.sum(payoff_matrices[1] * np.outer(strategy1, strategy2))
        
        return (payoff1, payoff2)
    
    def analyze_game_stability(self, payoff_matrices: List[np.ndarray],
                             equilibrium: Tuple) -> Dict[str, Any]:
        """게임 안정성 분석"""
        pure_equilibria = self.find_pure_strategy_nash(payoff_matrices)
        mixed_equilibrium = self.calculate_mixed_strategy_nash(payoff_matrices)
        
        analysis = {
            'total_pure_equilibria': len(pure_equilibria),
            'pure_equilibria': pure_equilibria,
            'has_mixed_equilibrium': 'player1_strategy' in mixed_equilibrium,
            'game_type': self._classify_game_type(payoff_matrices),
            'stability_score': self._calculate_stability_score(pure_equilibria, payoff_matrices)
        }
        
        if analysis['has_mixed_equilibrium']:
            analysis['mixed_equilibrium'] = mixed_equilibrium
        
        return analysis
    
    def _classify_game_type(self, payoff_matrices: List[np.ndarray]) -> str:
        """게임 유형 분류"""
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        # 제로섬 게임 확인
        if np.allclose(player1_payoffs + player2_payoffs, 0):
            return "Zero-sum"
        
        # 협조 게임 확인 (모든 칸에서 두 플레이어 모두 양의 보상)
        if np.all(player1_payoffs > 0) and np.all(player2_payoffs > 0):
            return "Coordination"
        
        # 죄수의 딜레마 유형 확인 (2x2 게임의 경우)
        if player1_payoffs.shape == (2, 2):
            if (player1_payoffs[0, 0] > player1_payoffs[1, 0] and
                player1_payoffs[1, 1] > player1_payoffs[0, 1] and
                player2_payoffs[0, 0] > player2_payoffs[0, 1] and
                player2_payoffs[1, 1] > player2_payoffs[1, 0]):
                return "Prisoner's Dilemma"
        
        return "General"
    
    def _calculate_stability_score(self, equilibria: List, payoff_matrices: List[np.ndarray]) -> float:
        """안정성 점수 계산"""
        if not equilibria:
            return 0.0
        
        # 균형점이 많을수록 불안정
        base_score = 1.0 / (1 + len(equilibria))
        
        # 보상의 분산이 클수록 불안정
        all_payoffs = [payoff_matrices[0].flatten(), payoff_matrices[1].flatten()]
        variance_penalty = np.mean([np.var(p) for p in all_payoffs]) / 100
        
        return max(0.0, base_score - variance_penalty)

# 사용 예시
def demonstrate_nash_equilibrium():
    """내쉬 균형 데모"""
    solver = NashEquilibriumSolver()
    
    # 죄수의 딜레마 게임
    player1_payoffs = np.array([[3, 0], [5, 1]])  # (협조, 배신) x (협조, 배신)
    player2_payoffs = np.array([[3, 5], [0, 1]])
    
    payoff_matrices = [player1_payoffs, player2_payoffs]
    
    # 순수 전략 균형 찾기
    pure_nash = solver.find_pure_strategy_nash(payoff_matrices)
    print(f"Pure Strategy Nash Equilibria: {pure_nash}")
    
    # 혼합 전략 균형 계산
    mixed_nash = solver.calculate_mixed_strategy_nash(payoff_matrices)
    print(f"Mixed Strategy Nash Equilibrium: {mixed_nash}")
    
    # 게임 분석
    analysis = solver.analyze_game_stability(payoff_matrices, pure_nash[0] if pure_nash else None)
    print(f"Game Analysis: {analysis}")