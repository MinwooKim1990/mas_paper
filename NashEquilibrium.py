# Example: Nash Equilibrium Implementation
import numpy as np
from typing import List, Tuple, Dict, Any
from itertools import product
from scipy.optimize import linprog

class NashEquilibriumSolver:
    """Calculates and analyzes Nash Equilibrium."""
    
    def __init__(self):
        self.games_history = []
        self.equilibria_found = []
    
    def find_pure_strategy_nash(self, payoff_matrices: List[np.ndarray]) -> List[Tuple]:
        """Finds pure strategy Nash equilibria."""
        if len(payoff_matrices) != 2:
            raise ValueError("Currently supports only 2-player games")
        
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        m, n = player1_payoffs.shape
        nash_equilibria = []
        
        # Check all strategy combinations
        for i in range(m):
            for j in range(n):
                is_nash = True
                
                # Check for Player 1's best response
                player1_current = player1_payoffs[i, j]
                for k in range(m):
                    if k != i and player1_payoffs[k, j] > player1_current:
                        is_nash = False
                        break
                
                if not is_nash:
                    continue
                
                # Check for Player 2's best response
                player2_current = player2_payoffs[i, j]
                for l in range(n):
                    if l != j and player2_payoffs[i, l] > player2_current:
                        is_nash = False
                        break
                
                if is_nash:
                    nash_equilibria.append((i, j))
        
        return nash_equilibria
    
    def calculate_mixed_strategy_nash(self, payoff_matrices: List[np.ndarray]) -> Dict[str, Any]:
        """Calculates mixed strategy Nash equilibrium."""
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        m, n = player1_payoffs.shape
        
        # Calculate Player 1's mixed strategy
        # When Player 2 uses a mixed strategy with probability q,
        # the expected payoffs for Player 1's pure strategies must be equal.
        
        if n > 1:
            # Set up Player 2's indifference condition
            A_eq = []
            b_eq = []
            
            for i in range(m - 1):
                row = []
                for j in range(n):
                    row.append(player1_payoffs[i, j] - player1_payoffs[i + 1, j])
                A_eq.append(row)
                b_eq.append(0)
            
            # Sum of probabilities must be 1
            A_eq.append([1] * n)
            b_eq.append(1)
            
            # All probabilities must be non-negative
            bounds = [(0, 1) for _ in range(n)]
            
            try:
                result = linprog(
                    c=[0] * n,  # Objective function (irrelevant)
                    A_eq=A_eq,
                    b_eq=b_eq,
                    bounds=bounds,
                    method='highs'
                )
                
                if result.success:
                    player2_mixed = result.x
                    
                    # Calculate Player 1's mixed strategy similarly
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
        """Calculates Player 1's mixed strategy."""
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
        
        # Default: uniform distribution
        return np.ones(m) / m
    
    def _calculate_expected_payoffs(self, payoff_matrices: List[np.ndarray],
                                  strategy1: np.ndarray, strategy2: np.ndarray) -> Tuple[float, float]:
        """Calculates expected payoffs."""
        payoff1 = np.sum(payoff_matrices[0] * np.outer(strategy1, strategy2))
        payoff2 = np.sum(payoff_matrices[1] * np.outer(strategy1, strategy2))
        
        return (payoff1, payoff2)
    
    def analyze_game_stability(self, payoff_matrices: List[np.ndarray],
                             equilibrium: Tuple) -> Dict[str, Any]:
        """Analyzes game stability."""
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
        """Classifies the game type."""
        player1_payoffs = payoff_matrices[0]
        player2_payoffs = payoff_matrices[1]
        
        # Check for zero-sum game
        if np.allclose(player1_payoffs + player2_payoffs, 0):
            return "Zero-sum"
        
        # Check for coordination game (both players have positive payoffs in all cells)
        if np.all(player1_payoffs > 0) and np.all(player2_payoffs > 0):
            return "Coordination"
        
        # Check for Prisoner's Dilemma type (for 2x2 games)
        if player1_payoffs.shape == (2, 2):
            if (player1_payoffs[0, 0] > player1_payoffs[1, 0] and
                player1_payoffs[1, 1] > player1_payoffs[0, 1] and
                player2_payoffs[0, 0] > player2_payoffs[0, 1] and
                player2_payoffs[1, 1] > player2_payoffs[1, 0]):
                return "Prisoner's Dilemma"
        
        return "General"
    
    def _calculate_stability_score(self, equilibria: List, payoff_matrices: List[np.ndarray]) -> float:
        """Calculates stability score."""
        if not equilibria:
            return 0.0
        
        # More equilibria means less stability
        base_score = 1.0 / (1 + len(equilibria))
        
        # Higher variance in payoffs means less stability
        all_payoffs = [payoff_matrices[0].flatten(), payoff_matrices[1].flatten()]
        variance_penalty = np.mean([np.var(p) for p in all_payoffs]) / 100
        
        return max(0.0, base_score - variance_penalty)

if __name__ == "__main__":
    def demonstrate_nash_equilibrium():
        """Demonstrates Nash Equilibrium."""
        solver = NashEquilibriumSolver()

        # Prisoner's Dilemma game
        player1_payoffs = np.array([[3, 0], [5, 1]])  # (Cooperate, Defect) x (Cooperate, Defect)
        player2_payoffs = np.array([[3, 5], [0, 1]])

        payoff_matrices = [player1_payoffs, player2_payoffs]

        # Find pure strategy equilibrium
        pure_nash = solver.find_pure_strategy_nash(payoff_matrices)
        print(f"Pure Strategy Nash Equilibria: {pure_nash}")

        # Calculate mixed strategy equilibrium
        mixed_nash = solver.calculate_mixed_strategy_nash(payoff_matrices)
        print(f"Mixed Strategy Nash Equilibrium: {mixed_nash}")

        # Analyze the game
        analysis = solver.analyze_game_stability(payoff_matrices, pure_nash[0] if pure_nash else None)
        print(f"Game Analysis: {analysis}")

    demonstrate_nash_equilibrium()