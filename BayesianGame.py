# Example: Bayesian Game Implementation
import random
from typing import Dict, List, Callable, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PlayerType:
    """Defines a player type."""
    type_id: str
    probability: float
    payoff_function: Callable[[str, str, str], float]  # (own_action, opponent_action, opponent_type) -> payoff
    
@dataclass
class BayesianGameResult:
    """Result of a Bayesian game."""
    player_strategies: Dict[str, Dict[str, str]]  # {player_id: {type: action}}
    expected_payoffs: Dict[str, float]
    equilibrium_type: str
    convergence_iterations: int

class BayesianGameSolver:
    """A solver for Bayesian games."""
    
    def __init__(self):
        self.game_history = []
        self.belief_updating_history = []
    
    def setup_game(self, player_types: Dict[str, List[PlayerType]], 
                   actions: Dict[str, List[str]]) -> Dict[str, Any]:
        """Sets up the game."""
        game_config = {
            'players': list(player_types.keys()),
            'player_types': player_types,
            'actions': actions,
            'type_probabilities': self._extract_type_probabilities(player_types)
        }
        
        return game_config
    
    def _extract_type_probabilities(self, player_types: Dict[str, List[PlayerType]]) -> Dict[str, Dict[str, float]]:
        """Extracts type probabilities."""
        probabilities = {}
        for player_id, types in player_types.items():
            probabilities[player_id] = {ptype.type_id: ptype.probability for ptype in types}
        return probabilities
    
    def calculate_bayesian_nash_equilibrium(self, game_config: Dict[str, Any], 
                                          max_iterations: int = 100) -> BayesianGameResult:
        """Calculates the Bayesian Nash Equilibrium."""
        players = game_config['players']
        player_types = game_config['player_types']
        actions = game_config['actions']
        
        # Initial strategy (random)
        strategies = {}
        for player_id in players:
            strategies[player_id] = {}
            for ptype in player_types[player_id]:
                strategies[player_id][ptype.type_id] = random.choice(actions[player_id])
        
        # Iterative best response
        for iteration in range(max_iterations):
            new_strategies = {}
            strategy_changed = False
            
            for player_id in players:
                new_strategies[player_id] = {}
                
                for ptype in player_types[player_id]:
                    # Calculate expected value for each action
                    action_values = {}
                    
                    for action in actions[player_id]:
                        expected_payoff = self._calculate_expected_payoff(
                            player_id, ptype, action, strategies, game_config
                        )
                        action_values[action] = expected_payoff
                    
                    # Choose the best action
                    best_action = max(action_values.keys(), key=lambda a: action_values[a])
                    new_strategies[player_id][ptype.type_id] = best_action
                    
                    # Check for strategy change
                    if strategies[player_id][ptype.type_id] != best_action:
                        strategy_changed = True
            
            strategies = new_strategies
            
            # Check for convergence
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
        """Calculates the expected payoff."""
        expected_payoff = 0.0
        players = game_config['players']
        player_types = game_config['player_types']
        
        # Probabilistic calculation over other players' types and actions
        for opponent_id in players:
            if opponent_id == player_id:
                continue
                
            for opponent_type in player_types[opponent_id]:
                opponent_action = strategies[opponent_id][opponent_type.type_id]
                
                # Probability of the opponent's type
                type_prob = opponent_type.probability
                
                # Payoff for this combination
                payoff = player_type.payoff_function(action, opponent_action, opponent_type.type_id)
                
                expected_payoff += type_prob * payoff
        
        return expected_payoff
    
    def _calculate_final_expected_payoffs(self, strategies: Dict, game_config: Dict) -> Dict[str, float]:
        """Calculates the final expected payoffs."""
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
        """Simulates Bayesian learning."""
        players = game_config['players']
        player_types = game_config['player_types']
        actions = game_config['actions']
        
        # Initial beliefs (prior probabilities)
        beliefs = {}
        for player_id in players:
            beliefs[player_id] = {}
            for opponent_id in players:
                if opponent_id != player_id:
                    beliefs[player_id][opponent_id] = {
                        ptype.type_id: ptype.probability 
                        for ptype in player_types[opponent_id]
                    }
        
        # Game record
        game_history = []
        belief_history = []
        
        for round_num in range(num_rounds):
            # Determine the actual type of each player
            actual_types = {}
            for player_id in players:
                type_probs = [ptype.probability for ptype in player_types[player_id]]
                chosen_type = random.choices(player_types[player_id], weights=type_probs)[0]
                actual_types[player_id] = chosen_type
            
            # Choose actions based on current beliefs
            round_actions = {}
            for player_id in players:
                ptype = actual_types[player_id]
                # Calculate the best action based on beliefs
                best_action = self._choose_action_based_on_beliefs(
                    player_id, ptype, beliefs[player_id], game_config
                )
                round_actions[player_id] = best_action
            
            # Observe results and update beliefs
            for player_id in players:
                for opponent_id in players:
                    if opponent_id != player_id:
                        observed_action = round_actions[opponent_id]
                        # Update beliefs using Bayes' rule
                        beliefs[player_id][opponent_id] = self._update_beliefs(
                            beliefs[player_id][opponent_id],
                            observed_action,
                            player_types[opponent_id],
                            actions[opponent_id]
                        )
            
            # Save records
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
        """Chooses an action based on beliefs."""
        actions = game_config['actions'][player_id]
        action_values = {}
        
        for action in actions:
            expected_value = 0.0
            
            # For all opponents
            for opponent_id, opponent_beliefs in beliefs.items():
                for opponent_type_id, type_prob in opponent_beliefs.items():
                    # Estimate the probability of the opponent choosing each action (simplified)
                    opponent_actions = game_config['actions'][opponent_id]
                    for opponent_action in opponent_actions:
                        action_prob = 1.0 / len(opponent_actions)  # Assume uniform distribution
                        
                        payoff = player_type.payoff_function(action, opponent_action, opponent_type_id)
                        expected_value += type_prob * action_prob * payoff
            
            action_values[action] = expected_value
        
        return max(action_values.keys(), key=lambda a: action_values[a])
    
    def _update_beliefs(self, current_beliefs: Dict[str, float], observed_action: str,
                       opponent_types: List[PlayerType], possible_actions: List[str]) -> Dict[str, float]:
        """Updates beliefs using Bayes' rule."""
        updated_beliefs = {}
        total_likelihood = 0.0
        
        # Calculate likelihood for each type
        likelihoods = {}
        for ptype in opponent_types:
            type_id = ptype.type_id
            prior = current_beliefs[type_id]
            
            # Probability that this type would choose the observed action (simplified: uniform)
            likelihood = 1.0 / len(possible_actions)
            
            likelihoods[type_id] = prior * likelihood
            total_likelihood += likelihoods[type_id]
        
        # Normalize (Bayes' rule)
        if total_likelihood > 0:
            for type_id in current_beliefs.keys():
                updated_beliefs[type_id] = likelihoods[type_id] / total_likelihood
        else:
            updated_beliefs = current_beliefs
        
        return updated_beliefs
    
    def _calculate_round_payoffs(self, actual_types: Dict, actions: Dict) -> Dict[str, float]:
        """Calculates round payoffs."""
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
        """Analyzes belief convergence."""
        if len(belief_history) < 2:
            return {'convergence': False, 'reason': 'Insufficient data'}
        
        # Analyze belief changes in the last 10 rounds
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

if __name__ == "__main__":
    def demonstrate_bayesian_game():
        """Demonstrates a Bayesian game."""
        solver = BayesianGameSolver()

        # Define player types (two types with different quality of information)
        def high_info_payoff(own_action, opponent_action, opponent_type):
            """Payoff function for high information type."""
            if own_action == "aggressive" and opponent_action == "passive":
                return 10
            elif own_action == "passive" and opponent_action == "aggressive":
                return 2
            elif own_action == opponent_action:
                return 5
            else:
                return 3

        def low_info_payoff(own_action, opponent_action, opponent_type):
            """Payoff function for low information type."""
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

        # Set up and solve the game
        game_config = solver.setup_game(player_types, actions)
        equilibrium = solver.calculate_bayesian_nash_equilibrium(game_config)

        print(f"Bayesian Nash Equilibrium: {equilibrium}")

        # Simulate learning
        learning_result = solver.simulate_bayesian_learning(game_config, num_rounds=30)
        print(f"Learning Result: {learning_result['learning_convergence']}")

    demonstrate_bayesian_game()