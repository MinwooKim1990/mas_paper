# Example: Mechanism Design Theory Implementation
from typing import Dict, List, Any
import random

class Agent:
    """An agent participating in the mechanism."""
    def __init__(self, agent_id: str, valuation: float = 0.0, cost: float = 0.0):
        self.agent_id = agent_id
        self.valuation = valuation  # True value for the item
        self.cost = cost            # Cost of performing a task
    
    def __repr__(self):
        return f"Agent(ID: {self.agent_id}, Valuation: {self.valuation:.2f}, Cost: {self.cost:.2f})"

class VCGAuction:
    """VCG (Vickrey-Clarke-Groves) Auction Implementation
    A mechanism that satisfies truthfulness and individual rationality."""
    
    def __init__(self, item_name: str = "Item"):
        self.item_name = item_name
        self.bids = {}  # {agent_id: bid_value}
    
    def add_bid(self, agent: Agent, bid_value: float):
        """Adds an agent's bid."""
        self.bids[agent.agent_id] = bid_value
        print(f"  - {agent.agent_id} bids {bid_value:.2f}")
    
    def run_auction(self):
        """Runs the VCG auction and calculates the results."""
        if not self.bids:
            return None, None, None
        
        # 1. Efficient allocation: the highest bidder wins
        winner_id = max(self.bids, key=self.bids.get)
        winning_bid = self.bids[winner_id]
        
        # 2. VCG payment: externality (second-highest bid)
        bids_without_winner = {aid: bid for aid, bid in self.bids.items() 
                              if aid != winner_id}
        payment = max(bids_without_winner.values()) if bids_without_winner else 0.0
        
        print(f"\n--- VCG Auction Results ({self.item_name}) ---")
        print(f"  Winner: {winner_id}")
        print(f"  Winning Bid: {winning_bid:.2f}")
        print(f"  VCG Payment: {payment:.2f}")
        
        # Check individual rationality
        if winning_bid >= payment:
            print(f"  [Individual Rationality Satisfied]: Participation gain = {winning_bid - payment:.2f}")
        
        # Discuss budget balance
        print(f"  [Budget Status]: System revenue = {payment:.2f}")
        
        return winner_id, winning_bid, payment

class TaskDistributionMechanism:
    """Multi-agent task distribution mechanism (applies inverse VCG)."""
    
    def __init__(self, tasks: list):
        self.tasks = tasks
        self.agent_costs = {}  # {agent_id: {task_id: cost}}
    
    def add_agent_costs(self, agent: Agent, task_costs: dict):
        """Reports the agent's costs for each task."""
        self.agent_costs[agent.agent_id] = task_costs
        print(f"  - {agent.agent_id} reports costs: {task_costs}")
    
    def run_distribution(self):
        """Runs the task distribution."""
        if not self.agent_costs or not self.tasks:
            return None, None
        
        allocations = {}  # {task_id: winner_id}
        payments = {}     # {agent_id: total_payment}
        
        print("\n--- Task Distribution Results ---")
        
        for task_id in self.tasks:
            # Find the agent with the lowest cost
            min_cost = float('inf')
            winner_agent_id = None
            
            for agent_id, costs in self.agent_costs.items():
                if task_id in costs and costs[task_id] < min_cost:
                    min_cost = costs[task_id]
                    winner_agent_id = agent_id
            
            if winner_agent_id:
                allocations[task_id] = winner_agent_id
                
                # VCG payment: second-lowest cost
                costs_without_winner = {
                    aid: costs[task_id] for aid, costs in self.agent_costs.items()
                    if aid != winner_agent_id and task_id in costs
                }
                second_min_cost = (min(costs_without_winner.values()) 
                                 if costs_without_winner else min_cost)
                
                payment_for_task = second_min_cost
                payments[winner_agent_id] = payments.get(winner_agent_id, 0.0) + payment_for_task
                
                print(f"  - '{task_id}': {winner_agent_id} (Cost: {min_cost:.2f}, Payment: {payment_for_task:.2f})")
                
                # Check individual rationality
                if payment_for_task >= min_cost:
                    profit = payment_for_task - min_cost
                    print(f"    [Individual Rationality Satisfied]: Profit = {profit:.2f}")
        
        return allocations, payments

def truthful_mechanism_demo():
    """Demonstrates a truthful mechanism."""
    print("=== Truthful Mechanism Demo ===")
    
    # VCG auction example
    auction = VCGAuction("Cloud Server Time")
    
    agent_a = Agent("AgentA", valuation=100)
    agent_b = Agent("AgentB", valuation=80)
    agent_c = Agent("AgentC", valuation=120)
    
    print("Running VCG Auction:")
    auction.add_bid(agent_a, agent_a.valuation)  # Bid truthfully
    auction.add_bid(agent_b, agent_b.valuation)
    auction.add_bid(agent_c, agent_c.valuation)
    
    winner, bid, payment = auction.run_auction()
    
    # Verify truthfulness: compare with the result of a false bid
    print(f"\nVerifying Truthfulness:")
    print(f"  Net profit with truthful bid: {bid - payment:.2f}")
    
    # What if agent_c bids falsely low?
    auction_false = VCGAuction("Test")
    auction_false.add_bid(agent_a, 100)
    auction_false.add_bid(agent_b, 80)
    auction_false.add_bid(agent_c, 90)  # False bid (actual value: 120)
    
    winner_false, bid_false, payment_false = auction_false.run_auction()
    if winner_false != agent_c.agent_id:
        print(f"  With false bid: Lost auction (Loss = -{agent_c.valuation - 0:.2f})")
    else:
        print(f"  Net profit with false bid: {bid_false - payment_false:.2f}")

def budget_balance_analysis():
    """Analyzes budget balance."""
    print("\n=== Budget Balance Analysis ===")
    
    # Scenario 1: System surplus
    auction1 = VCGAuction("Scenario1")
    auction1.bids = {"A": 100, "B": 80, "C": 60}
    winner1, bid1, payment1 = auction1.run_auction()
    
    surplus = payment1  # Money received by the system
    print(f"  System surplus: {surplus:.2f}")
    
    # Scenario 2: Budget analysis in task distribution
    tasks = ["Task1", "Task2"]
    mechanism = TaskDistributionMechanism(tasks)
    
    agent_x = Agent("X")
    agent_y = Agent("Y")
    
    mechanism.add_agent_costs(agent_x, {"Task1": 50, "Task2": 70})
    mechanism.add_agent_costs(agent_y, {"Task1": 60, "Task2": 40})
    
    allocations, payments = mechanism.run_distribution()
    
    total_actual_costs = 50 + 40  # Actual minimum cost
    total_payments = sum(payments.values())
    budget_deficit = total_payments - total_actual_costs
    
    print(f"\n  Actual total cost: {total_actual_costs:.2f}")
    print(f"  Total payments: {total_payments:.2f}")
    print(f"  Budget deficit: {budget_deficit:.2f}")

class IncentiveCompatibilityAnalyzer:
    """Incentive compatibility analyzer."""
    
    @staticmethod
    def analyze_truthfulness(true_values: List[float], 
                           mechanism_function: callable) -> Dict[str, Any]:
        """Analyzes truthfulness."""
        n_agents = len(true_values)
        results = {}
        
        # Truthful reporting
        truthful_outcome = mechanism_function(true_values)
        
        # Test false reporting for each agent
        for i in range(n_agents):
            best_utility = truthful_outcome['utilities'][i]
            best_report = true_values[i]
            
            # Try various false reports
            for false_value in [true_values[i] * 0.5, true_values[i] * 1.5, 
                              true_values[i] * 0.8, true_values[i] * 1.2]:
                if false_value == true_values[i]:
                    continue
                
                false_values = true_values.copy()
                false_values[i] = false_value
                false_outcome = mechanism_function(false_values)
                
                if false_outcome['utilities'][i] > best_utility:
                    best_utility = false_outcome['utilities'][i]
                    best_report = false_value
            
            results[f'agent_{i}'] = {
                'true_value': true_values[i],
                'best_report': best_report,
                'is_truthful': best_report == true_values[i],
                'utility_gain': best_utility - truthful_outcome['utilities'][i]
            }
        
        return results

def mechanism_design_comparison():
    """Compares different mechanisms."""
    print("\n=== Mechanism Design Comparison ===")
    
    # Test data
    true_values = [100, 80, 120, 90]
    
    def vcg_mechanism(values):
        """VCG mechanism simulation."""
        winner_idx = values.index(max(values))
        winner_value = max(values)
        
        # Second highest price
        second_price = sorted(values, reverse=True)[1]
        
        utilities = [0] * len(values)
        utilities[winner_idx] = winner_value - second_price
        
        return {
            'winner': winner_idx,
            'payment': second_price,
            'utilities': utilities,
            'efficiency': winner_value  # Social welfare
        }
    
    def first_price_auction(values):
        """First-price auction (not truthful)."""
        # Simple equilibrium strategy: bid 80% of your value
        bids = [v * 0.8 for v in values]
        winner_idx = bids.index(max(bids))
        winning_bid = max(bids)
        
        utilities = [0] * len(values)
        utilities[winner_idx] = values[winner_idx] - winning_bid
        
        return {
            'winner': winner_idx,
            'payment': winning_bid,
            'utilities': utilities,
            'efficiency': values[winner_idx]
        }
    
    # Run analysis
    analyzer = IncentiveCompatibilityAnalyzer()
    
    print("VCG Mechanism Truthfulness Analysis:")
    vcg_analysis = analyzer.analyze_truthfulness(true_values, vcg_mechanism)
    truthful_count = sum(1 for result in vcg_analysis.values() if result['is_truthful'])
    print(f"  Number of truthful agents: {truthful_count}/{len(true_values)}")
    
    print("\nFirst-Price Auction Truthfulness Analysis:")
    fpa_analysis = analyzer.analyze_truthfulness(true_values, first_price_auction)
    truthful_count_fpa = sum(1 for result in fpa_analysis.values() if result['is_truthful'])
    print(f"  Number of truthful agents: {truthful_count_fpa}/{len(true_values)}")
    
    # Compare efficiency
    vcg_result = vcg_mechanism(true_values)
    fpa_result = first_price_auction(true_values)
    
    print(f"\nEfficiency Comparison:")
    print(f"  VCG Social Welfare: {vcg_result['efficiency']:.2f}")
    print(f"  First-Price Auction Social Welfare: {fpa_result['efficiency']:.2f}")

# Main execution function
def demonstrate_mechanism_design():
    """Comprehensive demo of mechanism design theory."""
    print("=" * 50)
    print("Mechanism Design Theory Python Implementation Demo")
    print("=" * 50)
    
    truthful_mechanism_demo()
    budget_balance_analysis()
    mechanism_design_comparison()
    
    print("\n" + "=" * 50)
    print("Key Insights:")
    print("1. VCG achieves truthfulness and efficiency.")
    print("2. Budget balance is a trade-off with other properties.")
    print("3. Individual rationality ensures participation incentive.")
    print("4. The choice of mechanism depends on the goal.")
    print("=" * 50)

# Execute
if __name__ == "__main__":
    demonstrate_mechanism_design()