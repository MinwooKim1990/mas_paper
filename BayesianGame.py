# 예시: 베이지안 게임 (Bayesian Game) 구현
import random
from typing import Dict, List, Callable, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PlayerType:
    """플레이어 타입 정의"""
    type_id: str
    probability: float
    payoff_function: Callable[[str, str, str], float]  # (own_action, opponent_action, opponent_type) -> payoff
    
@dataclass
class BayesianGameResult:
    """베이지안 게임 결과"""
    player_strategies: Dict[str, Dict[str, str]]  # {player_id: {type: action}}
    expected_payoffs: Dict[str, float]
    equilibrium_type: str
    convergence_iterations: int

class BayesianGameSolver:
    """베이지안 게임 해결사"""
    
    def __init__(self):
        self.game_history = []
        self.belief_updating_history = []
    
    def setup_game(self, player_types: Dict[str, List[PlayerType]], 
                   actions: Dict[str, List[str]]) -> Dict[str, Any]:
        """게임 설정"""
        game_config = {
            'players': list(player_types.keys()),
            'player_types': player_types,
            'actions': actions,
            'type_probabilities': self._extract_type_probabilities(player_types)
        }
        
        return game_config
    
    def _extract_type_probabilities(self, player_types: Dict[str, List[PlayerType]]) -> Dict[str, Dict[str, float]]:
        """타입 확률 추출"""
        probabilities = {}
        for player_id, types in player_types.items():
            probabilities[player_id] = {ptype.type_id: ptype.probability for ptype in types}
        return probabilities
    
    def calculate_bayesian_nash_equilibrium(self, game_config: Dict[str, Any], 
                                          max_iterations: int = 100) -> BayesianGameResult:
        """베이지안 내쉬 균형 계산"""
        players = game_config['players']
        player_types = game_config['player_types']
        actions = game_config['actions']
        
        # 초기 전략 (무작위)
        strategies = {}
        for player_id in players:
            strategies[player_id] = {}
            for ptype in player_types[player_id]:
                strategies[player_id][ptype.type_id] = random.choice(actions[player_id])
        
        # 반복적 최선 반응
        for iteration in range(max_iterations):
            new_strategies = {}
            strategy_changed = False
            
            for player_id in players:
                new_strategies[player_id] = {}
                
                for ptype in player_types[player_id]:
                    # 각 액션에 대한 기댓값 계산
                    action_values = {}
                    
                    for action in actions[player_id]:
                        expected_payoff = self._calculate_expected_payoff(
                            player_id, ptype, action, strategies, game_config
                        )
                        action_values[action] = expected_payoff
                    
                    # 최적 액션 선택
                    best_action = max(action_values.keys(), key=lambda a: action_values[a])
                    new_strategies[player_id][ptype.type_id] = best_action
                    
                    # 전략 변화 확인
                    if strategies[player_id][ptype.type_id] != best_action:
                        strategy_changed = True
            
            strategies = new_strategies
            
            # 수렴 확인
            if not strategy_changed:
                return BayesianGameResult(
                    player_strategies=strategies,
                    expected_payoffs=self._calculate_final_expected_payoffs(strategies, game_config),
                    equilibrium_type="Pure Strategy Bayesian Nash",
                    convergence_iterations=iteration + 1
                )
        
        return BayesianGameResult(
            player_strategies=strategies,
            expected_payoffs=self._calculate_final_expected_payoffs(strategies, game_config),
            equilibrium_type="Approximate Equilibrium",
            convergence_iterations=max_iterations
        )

    def _calculate_expected_payoff(self, player_id: str, player_type: PlayerType, 
                                 action: str, strategies: Dict, game_config: Dict) -> float:
        """기댓값 계산"""
        expected_payoff = 0.0
        players = game_config['players']
        player_types = game_config['player_types']
        
        # 다른 플레이어들의 타입과 액션에 대한 확률적 계산
        for opponent_id in players:
            if opponent_id == player_id:
                continue
                
            for opponent_type in player_types[opponent_id]:
                opponent_action = strategies[opponent_id][opponent_type.type_id]
                
                # 상대방 타입에 대한 확률
                type_prob = opponent_type.probability
                
                # 이 조합에서의 보상
                payoff = player_type.payoff_function(action, opponent_action, opponent_type.type_id)
                
                expected_payoff += type_prob * payoff
        
        return expected_payoff
    
    def _calculate_final_expected_payoffs(self, strategies: Dict, game_config: Dict) -> Dict[str, float]:
        """최종 기댓값 계산"""
        players = game_config['players']
        player_types = game_config['player_types']
        
        final_payoffs = {}
        
        for player_id in players:
            total_expected = 0.0
            
            for ptype in player_types[player_id]:
                action = strategies[player_id][ptype.type_id]
                expected_payoff = self._calculate_expected_payoff(
                    player_id, ptype, action, strategies, game_config
                )
                total_expected += ptype.probability * expected_payoff
            
            final_payoffs[player_id] = total_expected
        
        return final_payoffs
    
    def simulate_bayesian_learning(self, game_config: Dict[str, Any], 
                                 num_rounds: int = 50) -> Dict[str, Any]:
        """베이지안 학습 시뮬레이션"""
        players = game_config['players']
        player_types = game_config['player_types']
        actions = game_config['actions']
        
        # 초기 신념 (사전 확률)
        beliefs = {}
        for player_id in players:
            beliefs[player_id] = {}
            for opponent_id in players:
                if opponent_id != player_id:
                    beliefs[player_id][opponent_id] = {
                        ptype.type_id: ptype.probability 
                        for ptype in player_types[opponent_id]
                    }
        
        # 게임 기록
        game_history = []
        belief_history = []
        
        for round_num in range(num_rounds):
            # 각 플레이어의 실제 타입 결정
            actual_types = {}
            for player_id in players:
                type_probs = [ptype.probability for ptype in player_types[player_id]]
                chosen_type = random.choices(player_types[player_id], weights=type_probs)[0]
                actual_types[player_id] = chosen_type
            
            # 액션 선택 (현재 신념 기반)
            round_actions = {}
            for player_id in players:
                ptype = actual_types[player_id]
                # 신념을 바탕으로 최적 액션 계산
                best_action = self._choose_action_based_on_beliefs(
                    player_id, ptype, beliefs[player_id], game_config
                )
                round_actions[player_id] = best_action
            
            # 결과 관찰 및 신념 업데이트
            for player_id in players:
                for opponent_id in players:
                    if opponent_id != player_id:
                        observed_action = round_actions[opponent_id]
                        # 베이즈 규칙으로 신념 업데이트
                        beliefs[player_id][opponent_id] = self._update_beliefs(
                            beliefs[player_id][opponent_id],
                            observed_action,
                            player_types[opponent_id],
                            actions[opponent_id]
                        )
            
            # 기록 저장
            game_history.append({
                'round': round_num,
                'actual_types': {pid: atype.type_id for pid, atype in actual_types.items()},
                'actions': round_actions,
                'payoffs': self._calculate_round_payoffs(actual_types, round_actions)
            })
            
            belief_history.append({
                'round': round_num,
                'beliefs': beliefs.copy()
            })
        
        return {
            'game_history': game_history,
            'belief_evolution': belief_history,
            'final_beliefs': beliefs,
            'learning_convergence': self._analyze_belief_convergence(belief_history)
        }
    
    def _choose_action_based_on_beliefs(self, player_id: str, player_type: PlayerType,
                                      beliefs: Dict[str, Dict[str, float]], 
                                      game_config: Dict) -> str:
        """신념 기반 액션 선택"""
        actions = game_config['actions'][player_id]
        action_values = {}
        
        for action in actions:
            expected_value = 0.0
            
            # 모든 상대방에 대해
            for opponent_id, opponent_beliefs in beliefs.items():
                for opponent_type_id, type_prob in opponent_beliefs.items():
                    # 상대방이 각 액션을 선택할 확률 추정 (단순화)
                    opponent_actions = game_config['actions'][opponent_id]
                    for opponent_action in opponent_actions:
                        action_prob = 1.0 / len(opponent_actions)  # 균등 분포 가정
                        
                        payoff = player_type.payoff_function(action, opponent_action, opponent_type_id)
                        expected_value += type_prob * action_prob * payoff
            
            action_values[action] = expected_value
        
        return max(action_values.keys(), key=lambda a: action_values[a])
    
    def _update_beliefs(self, current_beliefs: Dict[str, float], observed_action: str,
                       opponent_types: List[PlayerType], possible_actions: List[str]) -> Dict[str, float]:
        """베이즈 규칙으로 신념 업데이트"""
        updated_beliefs = {}
        total_likelihood = 0.0
        
        # 각 타입에 대한 가능도 계산
        likelihoods = {}
        for ptype in opponent_types:
            type_id = ptype.type_id
            prior = current_beliefs[type_id]
            
            # 해당 타입이 관찰된 액션을 선택할 확률 (단순화: 균등 분포)
            likelihood = 1.0 / len(possible_actions)
            
            likelihoods[type_id] = prior * likelihood
            total_likelihood += likelihoods[type_id]
        
        # 정규화 (베이즈 규칙)
        if total_likelihood > 0:
            for type_id in current_beliefs.keys():
                updated_beliefs[type_id] = likelihoods[type_id] / total_likelihood
        else:
            updated_beliefs = current_beliefs
        
        return updated_beliefs
    
    def _calculate_round_payoffs(self, actual_types: Dict, actions: Dict) -> Dict[str, float]:
        """라운드 보상 계산"""
        payoffs = {}
        
        for player_id, ptype in actual_types.items():
            player_action = actions[player_id]
            total_payoff = 0.0
            
            for opponent_id, opponent_type in actual_types.items():
                if opponent_id != player_id:
                    opponent_action = actions[opponent_id]
                    payoff = ptype.payoff_function(player_action, opponent_action, opponent_type.type_id)
                    total_payoff += payoff
            
            payoffs[player_id] = total_payoff
        
        return payoffs
    
    def _analyze_belief_convergence(self, belief_history: List[Dict]) -> Dict[str, Any]:
        """신념 수렴 분석"""
        if len(belief_history) < 2:
            return {'convergence': False, 'reason': 'Insufficient data'}
        
        # 마지막 10라운드의 신념 변화 분석
        recent_history = belief_history[-10:]
        
        max_change = 0.0
        for i in range(1, len(recent_history)):
            for player_id in recent_history[i]['beliefs']:
                for opponent_id in recent_history[i]['beliefs'][player_id]:
                    for type_id in recent_history[i]['beliefs'][player_id][opponent_id]:
                        current = recent_history[i]['beliefs'][player_id][opponent_id][type_id]
                        previous = recent_history[i-1]['beliefs'][player_id][opponent_id][type_id]
                        change = abs(current - previous)
                        max_change = max(max_change, change)
        
        convergence_threshold = 0.01
        return {
            'convergence': max_change < convergence_threshold,
            'max_recent_change': max_change,
            'threshold': convergence_threshold
        }

# 사용 예시
def demonstrate_bayesian_game():
    """베이지안 게임 데모"""
    solver = BayesianGameSolver()
    
    # 플레이어 타입 정의 (정보의 질이 다른 두 타입)
    def high_info_payoff(own_action, opponent_action, opponent_type):
        """높은 정보 타입의 보상 함수"""
        if own_action == "aggressive" and opponent_action == "passive":
            return 10
        elif own_action == "passive" and opponent_action == "aggressive":
            return 2
        elif own_action == opponent_action:
            return 5
        else:
            return 3
    
    def low_info_payoff(own_action, opponent_action, opponent_type):
        """낮은 정보 타입의 보상 함수"""
        if own_action == "aggressive":
            return 6
        else:
            return 4
    
    player_types = {
        'player1': [
            PlayerType('high_info', 0.7, high_info_payoff),
            PlayerType('low_info', 0.3, low_info_payoff)
        ],
        'player2': [
            PlayerType('high_info', 0.6, high_info_payoff),
            PlayerType('low_info', 0.4, low_info_payoff)
        ]
    }
    
    actions = {
        'player1': ['aggressive', 'passive'],
        'player2': ['aggressive', 'passive']
    }
    
    # 게임 설정 및 해결
    game_config = solver.setup_game(player_types, actions)
    equilibrium = solver.calculate_bayesian_nash_equilibrium(game_config)
    
    print(f"Bayesian Nash Equilibrium: {equilibrium}")
    
    # 학습 시뮬레이션
    learning_result = solver.simulate_bayesian_learning(game_config, num_rounds=30)
    print(f"Learning Result: {learning_result['learning_convergence']}")