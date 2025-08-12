# A/B 테스팅 프레임워크
import numpy as np
from scipy import stats
from typing import Any, Dict, Tuple, List
import random

class ABTestFramework:
    """A/B 테스트 실행 및 분석 프레임워크"""
    
    def __init__(self, control_name: str = "Control", 
                 treatment_name: str = "Treatment"):
        self.control_name = control_name
        self.treatment_name = treatment_name
        self.control_data = []
        self.treatment_data = []
        
    def assign_users_to_groups(self, 
                              user_ids: List[str], 
                              split_ratio: float = 0.5) -> Dict[str, str]:
        """사용자를 무작위로 그룹에 할당"""
        assignments = {}
        
        for user_id in user_ids:
            if random.random() < split_ratio:
                assignments[user_id] = self.control_name
            else:
                assignments[user_id] = self.treatment_name
                
        return assignments
    
    def calculate_sample_size(self, 
                            baseline_rate: float,
                            expected_lift: float,
                            alpha: float = 0.05,
                            power: float = 0.8) -> int:
        """필요한 샘플 크기 계산"""
        from statsmodels.stats.power import tt_ind_solve_power
        
        # 효과 크기 계산
        effect_size = expected_lift / np.sqrt(
            baseline_rate * (1 - baseline_rate)
        )
        
        # 각 그룹당 필요한 샘플 크기
        sample_size_per_group = tt_ind_solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ratio=1,
            alternative='two-sided'
        )
        
        return int(np.ceil(sample_size_per_group))
    
    def add_observation(self, group: str, value: float):
        """관측값 추가"""
        if group == self.control_name:
            self.control_data.append(value)
        elif group == self.treatment_name:
            self.treatment_data.append(value)
        else:
            raise ValueError(f"Unknown group: {group}")
    
    def analyze_results(self) -> Dict[str, Any]:
        """A/B 테스트 결과 분석"""
        if len(self.control_data) < 2 or len(self.treatment_data) < 2:
            return {"error": "Insufficient data for analysis"}
        
        # 기본 통계량
        control_mean = np.mean(self.control_data)
        treatment_mean = np.mean(self.treatment_data)
        
        # t-test 수행
        t_stat, p_value = stats.ttest_ind(
            self.control_data, 
            self.treatment_data,
            equal_var=False  # Welch's t-test
        )
        
        # 효과 크기 (Cohen's d)
        pooled_std = np.sqrt(
            (np.var(self.control_data, ddof=1) + 
             np.var(self.treatment_data, ddof=1)) / 2
        )
        cohens_d = (treatment_mean - control_mean) / pooled_std
        
        # 신뢰구간
        ci_low, ci_high = stats.t.interval(
            0.95,
            len(self.control_data) + len(self.treatment_data) - 2,
            loc=(treatment_mean - control_mean),
            scale=pooled_std * np.sqrt(
                1/len(self.control_data) + 1/len(self.treatment_data)
            )
        )
        
        # 상대적 개선율
        relative_lift = ((treatment_mean - control_mean) / 
                        control_mean * 100)
        
        return {
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'relative_lift': relative_lift,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'confidence_interval': (ci_low, ci_high),
            'significant': p_value < 0.05,
            'sample_sizes': {
                self.control_name: len(self.control_data),
                self.treatment_name: len(self.treatment_data)
            }
        }

# 실제 사용 예시
def run_agent_ab_test():
    """에이전트 성능 A/B 테스트 실행"""
    
    # 테스트 프레임워크 초기화
    ab_test = ABTestFramework(
        control_name="GPT-4",
        treatment_name="Claude-3.5"
    )
    
    # 필요한 샘플 크기 계산
    # 기본 성공률 70%, 10% 개선 기대
    required_size = ab_test.calculate_sample_size(
        baseline_rate=0.70,
        expected_lift=0.07,  # 70% -> 77%
        alpha=0.05,
        power=0.8
    )
    
    print(f"Required sample size per group: {required_size}")
    
    # 사용자를 그룹에 할당
    user_ids = [f"user_{i}" for i in range(2000)]
    assignments = ab_test.assign_users_to_groups(user_ids)
    
    # 시뮬레이션: 각 에이전트의 성능 측정
    for user_id in user_ids:
        group = assignments[user_id]
        
        # 성능 시뮬레이션 (실제로는 실제 측정값 사용)
        if group == "GPT-4":
            # GPT-4 기본 성공률: 70%
            success = np.random.binomial(1, 0.70)
        else:
            # Claude-3.5 개선된 성공률: 77%
            success = np.random.binomial(1, 0.77)
        
        ab_test.add_observation(group, success)

    # 결과 분석
    results = ab_test.analyze_results()
    
    print("\nA/B Test Results:")
    print(f"GPT-4 Success Rate: {results['control_mean']:.2%}")
    print(f"Claude-3.5 Success Rate: {results['treatment_mean']:.2%}")
    print(f"Relative Improvement: {results['relative_lift']:.1f}%")
    print(f"P-value: {results['p_value']:.4f}")
    print(f"Cohen's d: {results['cohens_d']:.3f}")
    print(f"95% CI: [{results['confidence_interval'][0]:.3f}, "
          f"{results['confidence_interval'][1]:.3f}]")
    print(f"Statistically Significant: {results['significant']}")
    
    return results

# Sequential Testing (Early Stopping)
class SequentialABTest(ABTestFramework):
    """순차적 A/B 테스트 (조기 종료 가능)"""
    
    def check_early_stopping(self, 
                           alpha_spend: float = 0.0001) -> Tuple[bool, str]:
        """조기 종료 조건 확인"""
        if len(self.control_data) < 100:
            return False, "Insufficient data"
        
        # O'Brien-Fleming 경계 사용
        n_current = len(self.control_data)
        n_planned = 1000
        
        # 정보 비율
        info_frac = n_current / n_planned
        
        # 조정된 유의수준
        z_boundary = stats.norm.ppf(1 - alpha_spend/2) / np.sqrt(info_frac)
        
        # 현재 z-score 계산
        t_stat, _ = stats.ttest_ind(self.control_data, 
                                   self.treatment_data)
        
        if abs(t_stat) > z_boundary:
            return True, "Significant difference detected"
        
        return False, "Continue testing"
