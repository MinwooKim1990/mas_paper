# 성능 비교의 통계적 유의성 검증
import scipy.stats as stats
import numpy as np
from typing import Any, Dict, List, Tuple

class StatisticalAnalyzer:
    """통계적 분석 도구"""
    
    @staticmethod
    def compare_performance(baseline_data: List[float], 
                          new_data: List[float], 
                          alpha: float = 0.05) -> Dict[str, Any]:
        """두 성능 데이터의 통계적 비교"""
        
        # 기본 통계량
        baseline_mean = np.mean(baseline_data)
        new_mean = np.mean(new_data)
        
        # 정규성 검정
        baseline_normal = stats.shapiro(baseline_data)[1] > alpha
        new_normal = stats.shapiro(new_data)[1] > alpha
        
        # 등분산성 검정
        equal_variance = stats.levene(baseline_data, new_data)[1] > alpha
        
        # 적절한 검정 방법 선택
        if baseline_normal and new_normal:
            if equal_variance:
                # t-검정 (등분산)
                statistic, p_value = stats.ttest_ind(baseline_data, new_data)
                test_type = "Independent t-test (equal variance)"
            else:
                # Welch의 t-검정 (이분산)
                statistic, p_value = stats.ttest_ind(baseline_data, new_data, equal_var=False)
                test_type = "Welch's t-test (unequal variance)"
        else:
            # Mann-Whitney U 검정 (비모수)
            statistic, p_value = stats.mannwhitneyu(baseline_data, new_data, alternative='two-sided')
            test_type = "Mann-Whitney U test (non-parametric)"
        
        # 효과 크기 계산 (Cohen's d)
        pooled_std = np.sqrt(((len(baseline_data) - 1) * np.var(baseline_data, ddof=1) + 
                             (len(new_data) - 1) * np.var(new_data, ddof=1)) / 
                            (len(baseline_data) + len(new_data) - 2))
        effect_size = (new_mean - baseline_mean) / pooled_std if pooled_std != 0 else 0
        
        # 신뢰구간 계산
        confidence_interval = stats.t.interval(
            1 - alpha, 
            len(baseline_data) + len(new_data) - 2,
            loc=new_mean - baseline_mean,
            scale=pooled_std * np.sqrt(1/len(baseline_data) + 1/len(new_data))
        )
        
        return {
            'baseline_mean': baseline_mean,
            'new_mean': new_mean,
            'difference': new_mean - baseline_mean,
            'percent_change': ((new_mean - baseline_mean) / baseline_mean) * 100 if baseline_mean != 0 else 0,
            'test_type': test_type,
            'p_value': p_value,
            'significant': p_value < alpha,
            'effect_size': effect_size,
            'confidence_interval': confidence_interval,
            'interpretation': StatisticalAnalyzer._interpret_results(p_value, effect_size, alpha)
        }
    
    @staticmethod
    def _interpret_results(p_value: float, effect_size: float, alpha: float) -> str:
        """결과 해석"""
        if p_value >= alpha:
            return "No statistically significant difference found"
        
        # 효과 크기 해석 (Cohen's convention)
        if abs(effect_size) < 0.2:
            magnitude = "negligible"
        elif abs(effect_size) < 0.5:
            magnitude = "small"
        elif abs(effect_size) < 0.8:
            magnitude = "medium"
        else:
            magnitude = "large"
        
        direction = "improvement" if effect_size > 0 else "degradation"
        
        return f"Statistically significant {direction} with {magnitude} effect size"
    
    @staticmethod
    def power_analysis(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
        """표본 크기 결정을 위한 검정력 분석"""
        from statsmodels.stats.power import ttest_power
        
        # 필요한 표본 크기 계산
        sample_size = ttest_power(effect_size, power, alpha, alternative='two-sided')
        return int(np.ceil(sample_size))

class ExperimentalDesigner:
    """실험 설계 도구"""
    
    def __init__(self):
        self.experiments = {}
        self.results = {}
    
    def design_factorial_experiment(self, factors: Dict[str, List], replications: int = 3):
        """요인 실험 설계"""
        import itertools
        
        # 모든 요인 조합 생성
        factor_names = list(factors.keys())
        factor_levels = list(factors.values())
        
        combinations = list(itertools.product(*factor_levels))
        
        experimental_design = []
        for rep in range(replications):
            for combo in combinations:
                condition = dict(zip(factor_names, combo))
                condition['replication'] = rep + 1
                experimental_design.append(condition)
        
        # 무작위 순서로 섞기
        np.random.shuffle(experimental_design)
        
        return experimental_design
    
    def analyze_factorial_results(self, design: List[Dict], results: List[float]) -> Dict:
        """요인 실험 결과 분석"""
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        
        # 데이터프레임 생성
        df = pd.DataFrame(design)
        df['result'] = results
        
        # 주효과 분석
        main_effects = {}
        for factor in df.columns:
            if factor not in ['replication', 'result']:
                grouped = df.groupby(factor)['result'].mean()
                main_effects[factor] = {
                    'means': grouped.to_dict(),
                    'range': grouped.max() - grouped.min()
                }
        
        # 상호작용 효과 분석 (2-way)
        interaction_effects = {}
        factor_names = [col for col in df.columns if col not in ['replication', 'result']]
        
        for i in range(len(factor_names)):
            for j in range(i + 1, len(factor_names)):
                factor1, factor2 = factor_names[i], factor_names[j]
                interaction_name = f"{factor1}_x_{factor2}"
                
                grouped = df.groupby([factor1, factor2])['result'].mean()
                interaction_effects[interaction_name] = grouped.to_dict()
        
        return {
            'main_effects': main_effects,
            'interaction_effects': interaction_effects,
            'summary_statistics': df.groupby('replication')['result'].describe().to_dict()
        }

# 사용 예시
def conduct_performance_study():
    """성능 연구 수행 예시"""
    
    # 실험 설계
    designer = ExperimentalDesigner()
    factors = {
        'agent_count': [10, 50, 100],
        'message_size': ['small', 'medium', 'large'],
        'network_latency': [10, 50, 100]  # ms
    }
    
    experimental_design = designer.design_factorial_experiment(factors, replications=5)
    
    # 실험 실행 (시뮬레이션)
    results = []
    for condition in experimental_design:
        # 각 조건에서 성능 측정 (실제로는 벤치마크 실행)
        simulated_result = simulate_performance(condition)
        results.append(simulated_result)
    
    # 결과 분석
    analysis = designer.analyze_factorial_results(experimental_design, results)
    
    # 통계적 유의성 검증
    analyzer = StatisticalAnalyzer()
    
    # 베이스라인과 최적 조건 비교
    baseline_results = [r for r, c in zip(results, experimental_design) 
                       if c['agent_count'] == 10 and c['message_size'] == 'small']
    optimal_results = [r for r, c in zip(results, experimental_design) 
                      if c['agent_count'] == 100 and c['message_size'] == 'large']
    
    if baseline_results and optimal_results:
        comparison = analyzer.compare_performance(baseline_results, optimal_results)
        
        print("Performance Study Results:")
        print(f"Baseline mean: {comparison['baseline_mean']:.2f}")
        print(f"Optimal mean: {comparison['new_mean']:.2f}")
        print(f"Improvement: {comparison['percent_change']:.1f}%")
        print(f"Statistical significance: {comparison['significant']}")
        print(f"Interpretation: {comparison['interpretation']}")

def simulate_performance(condition: Dict) -> float:
    """성능 시뮬레이션 (예시)"""
    base_performance = 100
    
    # 에이전트 수 영향
    agent_effect = condition['agent_count'] * 0.5
    
    # 메시지 크기 영향
    size_effects = {'small': 1.0, 'medium': 0.8, 'large': 0.6}
    size_effect = size_effects[condition['message_size']]
    
    # 네트워크 지연 영향
    latency_effect = 1.0 - (condition['network_latency'] / 1000)
    
    # 노이즈 추가
    noise = np.random.normal(0, 5)
    
    return (base_performance + agent_effect) * size_effect * latency_effect + noise

# 베이지안 A/B 테스팅
class BayesianABTest:
    """베이지안 접근법을 사용한 A/B 테스트"""
    
    def __init__(self, alpha_prior=1, beta_prior=1):
        self.alpha_prior = alpha_prior
        self.beta_prior = beta_prior
    
    def analyze(self, conversions_a, visitors_a, conversions_b, visitors_b, n_samples=10000):
        """베이지안 A/B 테스트 분석"""
        # 베타 분포에서 샘플링
        samples_a = np.random.beta(
            self.alpha_prior + conversions_a,
            self.beta_prior + visitors_a - conversions_a,
            n_samples
        )
        samples_b = np.random.beta(
            self.alpha_prior + conversions_b,
            self.beta_prior + visitors_b - conversions_b,
            n_samples
        )
        
        # B가 A보다 좋을 확률
        prob_b_better = (samples_b > samples_a).mean()
        
        # 개선율 분포
        improvement = (samples_b - samples_a) / samples_a
        
        return {
            'prob_b_better': prob_b_better,
            'expected_improvement': improvement.mean(),
            'improvement_ci': np.percentile(improvement, [2.5, 97.5])
        }
