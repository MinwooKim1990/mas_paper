# 예시: 메커니즘 설계 이론 (Mechanism Design Theory) 구현
from typing import Dict, List, Any
import random

class Agent:
    """메커니즘에 참여하는 에이전트"""
    def __init__(self, agent_id: str, valuation: float = 0.0, cost: float = 0.0):
        self.agent_id = agent_id
        self.valuation = valuation  # 아이템에 대한 진실된 가치
        self.cost = cost            # 작업 수행 비용
    
    def __repr__(self):
        return f"Agent(ID: {self.agent_id}, 가치: {self.valuation:.2f}, 비용: {self.cost:.2f})"

class VCGAuction:
    """VCG (Vickrey-Clarke-Groves) 옥션 구현
    진실성 유도 및 개별 합리성을 만족하는 메커니즘"""
    
    def __init__(self, item_name: str = "아이템"):
        self.item_name = item_name
        self.bids = {}  # {agent_id: bid_value}
    
    def add_bid(self, agent: Agent, bid_value: float):
        """에이전트의 입찰 추가"""
        self.bids[agent.agent_id] = bid_value
        print(f"  - {agent.agent_id}가 {bid_value:.2f} 입찰")
    
    def run_auction(self):
        """VCG 옥션 실행 및 결과 계산"""
        if not self.bids:
            return None, None, None
        
        # 1. 효율적 할당: 최고 입찰자가 낙찰
        winner_id = max(self.bids, key=self.bids.get)
        winning_bid = self.bids[winner_id]
        
        # 2. VCG 지불액: 외부 효과 (두 번째 최고 입찰가)
        bids_without_winner = {aid: bid for aid, bid in self.bids.items() 
                              if aid != winner_id}
        payment = max(bids_without_winner.values()) if bids_without_winner else 0.0
        
        print(f"\n--- VCG 옥션 결과 ({self.item_name}) ---")
        print(f"  낙찰자: {winner_id}")
        print(f"  낙찰 입찰가: {winning_bid:.2f}")
        print(f"  VCG 지불액: {payment:.2f}")
        
        # 개별 합리성 확인
        if winning_bid >= payment:
            print(f"  [개별 합리성 만족]: 참여 이득 = {winning_bid - payment:.2f}")
        
        # 예산 균형 논의
        print(f"  [예산 상황]: 시스템 수입 = {payment:.2f}")
        
        return winner_id, winning_bid, payment

class TaskDistributionMechanism:
    """다중 에이전트 작업 분배 메커니즘 (역 VCG 적용)"""
    
    def __init__(self, tasks: list):
        self.tasks = tasks
        self.agent_costs = {}  # {agent_id: {task_id: cost}}
    
    def add_agent_costs(self, agent: Agent, task_costs: dict):
        """에이전트의 작업별 비용 보고"""
        self.agent_costs[agent.agent_id] = task_costs
        print(f"  - {agent.agent_id} 비용 보고: {task_costs}")
    
    def run_distribution(self):
        """작업 분배 실행"""
        if not self.agent_costs or not self.tasks:
            return None, None
        
        allocations = {}  # {task_id: winner_id}
        payments = {}     # {agent_id: total_payment}
        
        print("\n--- 작업 분배 결과 ---")
        
        for task_id in self.tasks:
            # 최저 비용 에이전트 찾기
            min_cost = float('inf')
            winner_agent_id = None
            
            for agent_id, costs in self.agent_costs.items():
                if task_id in costs and costs[task_id] < min_cost:
                    min_cost = costs[task_id]
                    winner_agent_id = agent_id
            
            if winner_agent_id:
                allocations[task_id] = winner_agent_id
                
                # VCG 지불액: 두 번째 최저 비용
                costs_without_winner = {
                    aid: costs[task_id] for aid, costs in self.agent_costs.items()
                    if aid != winner_agent_id and task_id in costs
                }
                second_min_cost = (min(costs_without_winner.values()) 
                                 if costs_without_winner else min_cost)
                
                payment_for_task = second_min_cost
                payments[winner_agent_id] = payments.get(winner_agent_id, 0.0) + payment_for_task
                
                print(f"  - '{task_id}': {winner_agent_id} (비용: {min_cost:.2f}, 지불: {payment_for_task:.2f})")
                
                # 개별 합리성 확인
                if payment_for_task >= min_cost:
                    profit = payment_for_task - min_cost
                    print(f"    [개별 합리성 만족]: 이익 = {profit:.2f}")
        
        return allocations, payments

def truthful_mechanism_demo():
    """진실성 유도 메커니즘 데모"""
    print("=== 진실성 유도 메커니즘 데모 ===")
    
    # VCG 옥션 예시
    auction = VCGAuction("클라우드 서버 시간")
    
    agent_a = Agent("에이전트A", valuation=100)
    agent_b = Agent("에이전트B", valuation=80)
    agent_c = Agent("에이전트C", valuation=120)
    
    print("VCG 옥션 진행:")
    auction.add_bid(agent_a, agent_a.valuation)  # 진실하게 입찰
    auction.add_bid(agent_b, agent_b.valuation)
    auction.add_bid(agent_c, agent_c.valuation)
    
    winner, bid, payment = auction.run_auction()
    
    # 진실성 검증: 거짓 입찰 시 결과 비교
    print(f"\n진실성 검증:")
    print(f"  진실 입찰 시 순이익: {bid - payment:.2f}")
    
    # 만약 agent_c가 거짓으로 낮게 입찰한다면?
    auction_false = VCGAuction("테스트")
    auction_false.add_bid(agent_a, 100)
    auction_false.add_bid(agent_b, 80)
    auction_false.add_bid(agent_c, 90)  # 거짓 입찰 (실제 가치: 120)
    
    winner_false, bid_false, payment_false = auction_false.run_auction()
    if winner_false != agent_c.agent_id:
        print(f"  거짓 입찰 시: 낙찰 실패 (손실 = -{agent_c.valuation - 0:.2f})")
    else:
        print(f"  거짓 입찰 시 순이익: {bid_false - payment_false:.2f}")

def budget_balance_analysis():
    """예산 균형 분석"""
    print("\n=== 예산 균형 분석 ===")
    
    # 시나리오 1: 시스템 흑자
    auction1 = VCGAuction("시나리오1")
    auction1.bids = {"A": 100, "B": 80, "C": 60}
    winner1, bid1, payment1 = auction1.run_auction()
    
    surplus = payment1  # 시스템이 받는 돈
    print(f"  시스템 흑자: {surplus:.2f}")
    
    # 시나리오 2: 작업 분배에서의 예산 분석
    tasks = ["작업1", "작업2"]
    mechanism = TaskDistributionMechanism(tasks)
    
    agent_x = Agent("X")
    agent_y = Agent("Y")
    
    mechanism.add_agent_costs(agent_x, {"작업1": 50, "작업2": 70})
    mechanism.add_agent_costs(agent_y, {"작업1": 60, "작업2": 40})
    
    allocations, payments = mechanism.run_distribution()
    
    total_actual_costs = 50 + 40  # 실제 최소 비용
    total_payments = sum(payments.values())
    budget_deficit = total_payments - total_actual_costs
    
    print(f"\n  실제 총 비용: {total_actual_costs:.2f}")
    print(f"  총 지불액: {total_payments:.2f}")
    print(f"  예산 적자: {budget_deficit:.2f}")

class IncentiveCompatibilityAnalyzer:
    """인센티브 호환성 분석기"""
    
    @staticmethod
    def analyze_truthfulness(true_values: List[float], 
                           mechanism_function: callable) -> Dict[str, Any]:
        """진실성 분석"""
        n_agents = len(true_values)
        results = {}
        
        # 진실한 보고
        truthful_outcome = mechanism_function(true_values)
        
        # 각 에이전트의 거짓 보고 테스트
        for i in range(n_agents):
            best_utility = truthful_outcome['utilities'][i]
            best_report = true_values[i]
            
            # 다양한 거짓 보고 시도
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
    """다양한 메커니즘 비교"""
    print("\n=== 메커니즘 설계 비교 ===")
    
    # 테스트 데이터
    true_values = [100, 80, 120, 90]
    
    def vcg_mechanism(values):
        """VCG 메커니즘 시뮬레이션"""
        winner_idx = values.index(max(values))
        winner_value = max(values)
        
        # 두 번째 최고가
        second_price = sorted(values, reverse=True)[1]
        
        utilities = [0] * len(values)
        utilities[winner_idx] = winner_value - second_price
        
        return {
            'winner': winner_idx,
            'payment': second_price,
            'utilities': utilities,
            'efficiency': winner_value  # 사회적 후생
        }
    
    def first_price_auction(values):
        """1차 가격 옥션 (비진실성)"""
        # 간단한 균형 전략: 자신의 가치의 80% 입찰
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
    
    # 분석 실행
    analyzer = IncentiveCompatibilityAnalyzer()
    
    print("VCG 메커니즘 진실성 분석:")
    vcg_analysis = analyzer.analyze_truthfulness(true_values, vcg_mechanism)
    truthful_count = sum(1 for result in vcg_analysis.values() if result['is_truthful'])
    print(f"  진실한 에이전트 수: {truthful_count}/{len(true_values)}")
    
    print("\n1차 가격 옥션 진실성 분석:")
    fpa_analysis = analyzer.analyze_truthfulness(true_values, first_price_auction)
    truthful_count_fpa = sum(1 for result in fpa_analysis.values() if result['is_truthful'])
    print(f"  진실한 에이전트 수: {truthful_count_fpa}/{len(true_values)}")
    
    # 효율성 비교
    vcg_result = vcg_mechanism(true_values)
    fpa_result = first_price_auction(true_values)
    
    print(f"\n효율성 비교:")
    print(f"  VCG 사회적 후생: {vcg_result['efficiency']:.2f}")
    print(f"  1차 가격 옥션 사회적 후생: {fpa_result['efficiency']:.2f}")

# 메인 실행 함수
def demonstrate_mechanism_design():
    """메커니즘 설계 이론 종합 데모"""
    print("=" * 50)
    print("메커니즘 설계 이론 Python 구현 데모")
    print("=" * 50)
    
    truthful_mechanism_demo()
    budget_balance_analysis()
    mechanism_design_comparison()
    
    print("\n" + "=" * 50)
    print("핵심 통찰:")
    print("1. VCG는 진실성 유도와 효율성을 달성")
    print("2. 예산 균형은 다른 속성과 트레이드오프")
    print("3. 개별 합리성은 참여 인센티브 보장")
    print("4. 메커니즘 선택은 목표에 따라 결정")
    print("=" * 50)

# 실행
if __name__ == "__main__":
    demonstrate_mechanism_design()