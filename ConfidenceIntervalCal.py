# 신뢰구간과 불확실성 정량화
import numpy as np
from scipy import stats
from typing import Tuple, List, Dict
import warnings

class ConfidenceIntervalCalculator:
    """다양한 방법으로 신뢰구간 계산"""
    
    @staticmethod
    def parametric_ci(data: List[float], 
                     confidence: float = 0.95) -> Tuple[float, float]:
        """파라메트릭 신뢰구간 (정규분포 가정)"""
        n = len(data)
        mean = np.mean(data)
        std_err = stats.sem(data)
        
        # t-분포 사용
        t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin_error = t_critical * std_err
        
        return (mean - margin_error, mean + margin_error)
    
    @staticmethod
    def bootstrap_ci(data: List[float], 
                    confidence: float = 0.95,
                    n_bootstrap: int = 10000) -> Tuple[float, float]:
        """부트스트랩 신뢰구간 (분포 가정 없음)"""
        n = len(data)
        bootstrap_means = []
        
        # 부트스트랩 샘플링
        for _ in range(n_bootstrap):
            # 복원추출로 재샘플링
            resample = np.random.choice(data, size=n, replace=True)
            bootstrap_means.append(np.mean(resample))
        
        # 백분위수 방법
        alpha = 1 - confidence
        lower = np.percentile(bootstrap_means, alpha/2 * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        
        return (lower, upper)
    
    @staticmethod
    def wilson_score_ci(successes: int, 
                       trials: int, 
                       confidence: float = 0.95) -> Tuple[float, float]:
        """Wilson Score 신뢰구간 (이항 비율용)"""
        if trials == 0:
            return (0, 0)
        
        p_hat = successes / trials
        z = stats.norm.ppf((1 + confidence) / 2)
        z_squared = z ** 2
        
        denominator = 1 + z_squared / trials
        
        center = (p_hat + z_squared / (2 * trials)) / denominator
        
        margin = z * np.sqrt(
            p_hat * (1 - p_hat) / trials + 
            z_squared / (4 * trials ** 2)
        ) / denominator
        
        return (max(0, center - margin), min(1, center + margin))

class UncertaintyQuantification:
    """불확실성 정량화 도구"""
    
    def __init__(self, data: List[float]):
        self.data = np.array(data)
        
    def calculate_metrics(self) -> Dict[str, float]:
        """다양한 불확실성 메트릭 계산"""
        metrics = {}
        
        # 중심 경향성
        metrics['mean'] = np.mean(self.data)
        metrics['median'] = np.median(self.data)
        metrics['mode'] = stats.mode(self.data, keepdims=True)[0][0]
        
        # 변동성 측정
        metrics['std'] = np.std(self.data, ddof=1)
        metrics['variance'] = np.var(self.data, ddof=1)
        metrics['cv'] = metrics['std'] / metrics['mean']  # 변동계수
        
        # 분포 형태
        metrics['skewness'] = stats.skew(self.data)
        metrics['kurtosis'] = stats.kurtosis(self.data)
        
        # 백분위수
        metrics['percentiles'] = {
            '25': np.percentile(self.data, 25),
            '50': np.percentile(self.data, 50),
            '75': np.percentile(self.data, 75),
            '95': np.percentile(self.data, 95)
        }
        
        return metrics
    
    def bayesian_credible_interval(self, 
                                 prior_alpha: float = 1, 
                                 prior_beta: float = 1,
                                 confidence: float = 0.95) -> Tuple[float, float]:
        """베이지안 신용구간 (이항 데이터용)"""
        # 데이터를 0과 1로 변환 (성공/실패)
        binary_data = (self.data > np.median(self.data)).astype(int)
        
        successes = np.sum(binary_data)
        failures = len(binary_data) - successes
        
        # 사후 분포 파라미터
        posterior_alpha = prior_alpha + successes
        posterior_beta = prior_beta + failures
        
        # 베타 분포의 신용구간
        alpha = 1 - confidence
        lower = stats.beta.ppf(alpha/2, posterior_alpha, posterior_beta)
        upper = stats.beta.ppf(1 - alpha/2, posterior_alpha, posterior_beta)
        
        return (lower, upper)
    
    def prediction_interval(self, 
                          confidence: float = 0.95,
                          n_future: int = 1) -> Tuple[float, float]:
        """예측 구간 계산"""
        mean = np.mean(self.data)
        std = np.std(self.data, ddof=1)
        n = len(self.data)
        
        # 예측 표준오차
        pred_std = std * np.sqrt(1 + 1/n + n_future/n)
        
        # t-분포 사용
        t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_critical * pred_std
        
        return (mean - margin, mean + margin)

# 실제 사용 예시
def analyze_agent_performance_uncertainty():
    """에이전트 성능의 불확실성 분석"""
    
    # 에이전트 응답 시간 데이터 (초)
    response_times = np.random.gamma(2, 0.5, 100)

    # 신뢰구간 계산
    ci_calc = ConfidenceIntervalCalculator()
    
    # 1. 파라메트릭 신뢰구간
    param_ci = ci_calc.parametric_ci(response_times)
    print(f"Parametric 95% CI: [{param_ci[0]:.3f}, {param_ci[1]:.3f}]")
    
    # 2. 부트스트랩 신뢰구간
    boot_ci = ci_calc.bootstrap_ci(response_times)
    print(f"Bootstrap 95% CI: [{boot_ci[0]:.3f}, {boot_ci[1]:.3f}]")
    
    # 3. 성공률 신뢰구간 (Wilson Score)
    successes = sum(1 for t in response_times if t < 1.0)
    wilson_ci = ci_calc.wilson_score_ci(successes, len(response_times))
    print(f"Success Rate 95% CI: [{wilson_ci[0]:.3f}, {wilson_ci[1]:.3f}]")
    
    # 불확실성 정량화
    uq = UncertaintyQuantification(response_times)
    metrics = uq.calculate_metrics()
    
    print("\nUncertainty Metrics:")
    print(f"Mean: {metrics['mean']:.3f}")
    print(f"Std Dev: {metrics['std']:.3f}")
    print(f"Coefficient of Variation: {metrics['cv']:.3f}")
    print(f"Skewness: {metrics['skewness']:.3f}")
    
    # 예측 구간
    pred_interval = uq.prediction_interval()
    print(f"\n95% Prediction Interval for next observation: "
          f"[{pred_interval[0]:.3f}, {pred_interval[1]:.3f}]")
    
    # 시각화 코드
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 6))
    plt.hist(response_times, bins=30, density=True, alpha=0.7, 
             label='Observed Data')
    plt.axvline(metrics['mean'], color='red', linestyle='--', 
                label=f'Mean: {metrics["mean"]:.2f}')
    plt.axvspan(param_ci[0], param_ci[1], alpha=0.3, color='green',
                label='95% CI')
    plt.xlabel('Response Time (seconds)')
    plt.ylabel('Density')
    plt.title('Agent Response Time Distribution with Uncertainty')
    plt.legend()
    plt.grid(True, alpha=0.3)