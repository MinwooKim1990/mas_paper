# 가설 검정 프레임워크
import numpy as np
from scipy import stats
from typing import Any, Dict, Tuple, List, Optional
from statsmodels.stats.multitest import multipletests

class HypothesisTestingFramework:
    """포괄적인 가설 검정 도구"""
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        self.test_results = []
        
    def normality_test(self, data: List[float]) -> Dict[str, Any]:
        """정규성 검정 (여러 방법 사용)"""
        results = {}
        
        # Shapiro-Wilk 검정
        shapiro_stat, shapiro_p = stats.shapiro(data)
        results['shapiro_wilk'] = {
            'statistic': shapiro_stat,
            'p_value': shapiro_p,
            'normal': shapiro_p > self.alpha
        }
        
        # Anderson-Darling 검정
        anderson_result = stats.anderson(data)
        results['anderson_darling'] = {
            'statistic': anderson_result.statistic,
            'critical_values': dict(zip(
                anderson_result.significance_level,
                anderson_result.critical_values
            ))
        }
        
        # Kolmogorov-Smirnov 검정
        ks_stat, ks_p = stats.kstest(data, 'norm', 
                                    args=(np.mean(data), np.std(data)))
        results['kolmogorov_smirnov'] = {
            'statistic': ks_stat,
            'p_value': ks_p,
            'normal': ks_p > self.alpha
        }
        
        return results
    
    def two_sample_test(self, 
                       group1: List[float], 
                       group2: List[float],
                       test_type: str = 'auto') -> Dict[str, Any]:
        """두 그룹 비교 검정"""
        results = {
            'group1_mean': np.mean(group1),
            'group2_mean': np.mean(group2),
            'difference': np.mean(group2) - np.mean(group1)
        }

        # 정규성 확인
        norm1 = self.normality_test(group1)['shapiro_wilk']['normal']
        norm2 = self.normality_test(group2)['shapiro_wilk']['normal']
        
        if test_type == 'auto':
            if norm1 and norm2:
                test_type = 'parametric'
            else:
                test_type = 'non_parametric'
        
        if test_type == 'parametric':
            # 등분산성 검정
            levene_stat, levene_p = stats.levene(group1, group2)
            equal_var = levene_p > self.alpha
            
            # t-검정
            t_stat, t_p = stats.ttest_ind(group1, group2, 
                                         equal_var=equal_var)
            
            results['test'] = 'Independent t-test' if equal_var else "Welch's t-test"
            results['statistic'] = t_stat
            results['p_value'] = t_p
            results['equal_variance'] = equal_var
            
        else:
            # Mann-Whitney U 검정
            u_stat, u_p = stats.mannwhitneyu(group1, group2, 
                                            alternative='two-sided')
            
            results['test'] = 'Mann-Whitney U test'
            results['statistic'] = u_stat
            results['p_value'] = u_p
        
        # 효과 크기
        pooled_std = np.sqrt((np.var(group1, ddof=1) + 
                            np.var(group2, ddof=1)) / 2)
        results['cohens_d'] = results['difference'] / pooled_std
        
        # 결론
        results['reject_null'] = results['p_value'] < self.alpha
        results['conclusion'] = self._interpret_results(results)
        
        self.test_results.append(results)
        return results
    
    def multiple_comparisons(self, 
                           groups: Dict[str, List[float]],
                           method: str = 'bonferroni') -> Dict[str, Any]:
        """다중 비교 검정"""
        group_names = list(groups.keys())
        n_groups = len(group_names)
        
        # 모든 쌍별 비교
        comparisons = []
        p_values = []
        
        for i in range(n_groups):
            for j in range(i + 1, n_groups):
                result = self.two_sample_test(
                    groups[group_names[i]], 
                    groups[group_names[j]]
                )
                
                comparisons.append({
                    'group1': group_names[i],
                    'group2': group_names[j],
                    'p_value': result['p_value'],
                    'difference': result['difference']
                })
                p_values.append(result['p_value'])
        
        # 다중 비교 보정
        if method == 'bonferroni':
            adjusted_alpha = self.alpha / len(comparisons)
            adjusted_p_values = [p * len(comparisons) for p in p_values]
        elif method == 'fdr':
            reject, adjusted_p_values, _, _ = multipletests(
                p_values, alpha=self.alpha, method='fdr_bh'
            )
        else:
            adjusted_p_values = p_values
            adjusted_alpha = self.alpha
        
        # 결과 업데이트
        for i, comp in enumerate(comparisons):
            comp['adjusted_p_value'] = min(adjusted_p_values[i], 1.0)
            comp['significant'] = comp['adjusted_p_value'] < self.alpha
        
        return {
            'method': method,
            'comparisons': comparisons,
            'n_comparisons': len(comparisons),
            'adjusted_alpha': adjusted_alpha if method == 'bonferroni' else self.alpha
        }
    
    def _interpret_results(self, results: Dict) -> str:
        """결과 해석"""
        if results['reject_null']:
            effect_size = abs(results['cohens_d'])
            if effect_size < 0.2:
                magnitude = "negligible"
            elif effect_size < 0.5:
                magnitude = "small"
            elif effect_size < 0.8:
                magnitude = "medium"
            else:
                magnitude = "large"
            
            direction = "higher" if results['difference'] > 0 else "lower"
            
            return (f"Statistically significant difference found "
                   f"(p={results['p_value']:.4f}). "
                   f"Group 2 shows {direction} performance with "
                   f"{magnitude} effect size (d={effect_size:.3f}).")
        else:
            return (f"No statistically significant difference found "
                   f"(p={results['p_value']:.4f}). "
                   f"Cannot reject the null hypothesis.")

# 실제 사용 예시
def test_multi_agent_performance():
    """멀티 에이전트 성능 가설 검정"""
    
    # 세 가지 에이전트 구성의 성능 데이터
    agent_configs = {
        'Single_Agent': np.random.normal(75, 10, 50),
        'Dual_Agent': np.random.normal(82, 8, 50),
        'Multi_Agent_5': np.random.normal(85, 12, 50)
    }
    
    # 가설 검정 프레임워크 초기화
    htf = HypothesisTestingFramework(alpha=0.05)
    
    # 정규성 검정
    print("Normality Tests:")
    for name, data in agent_configs.items():
        norm_result = htf.normality_test(data)
        print(f"{name}: Normal={norm_result['shapiro_wilk']['normal']}")
    
    # 다중 비교
    print("\nMultiple Comparisons (Bonferroni corrected):")
    multi_results = htf.multiple_comparisons(agent_configs, 
                                            method='bonferroni')
    
    for comp in multi_results['comparisons']:
        print(f"{comp['group1']} vs {comp['group2']}: "
              f"p={comp['adjusted_p_value']:.4f}, "
              f"significant={comp['significant']}")
