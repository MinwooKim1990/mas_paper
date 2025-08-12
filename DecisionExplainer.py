# 예시: 에이전트 의사결정 설명 시스템
import time
import statistics
from typing import Any, Dict, List


class DecisionExplainer:
    """에이전트 의사결정 설명 생성기"""
    
    def __init__(self):
        self.decision_history = []
        self.explanation_templates = {
            'rule_based': "Decision made based on rule: {rule}. Input values: {inputs}",
            'ml_based': "ML model predicted {prediction} with {confidence:.1%} confidence. Key factors: {factors}",
            'collaborative': "Decision reached through consensus with {agent_count} agents. Agreement level: {agreement:.1%}",
            'human_guided': "Following human instruction: {instruction}. Executed with parameters: {parameters}"
        }
    
    def explain_decision(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """의사결정 설명 생성"""
        decision_type = decision_context.get('type', 'unknown')
        
        explanation = {
            'decision_id': decision_context.get('decision_id'),
            'timestamp': time.time(),
            'agent_id': decision_context.get('agent_id'),
            'decision_type': decision_type,
            'input_data': decision_context.get('inputs', {}),
            'output': decision_context.get('output'),
            'reasoning_steps': self._generate_reasoning_steps(decision_context),
            'confidence_level': decision_context.get('confidence', 0.0),
            'alternative_options': decision_context.get('alternatives', []),
            'human_readable_explanation': self._generate_human_explanation(decision_context)
        }
        
        self.decision_history.append(explanation)
        return explanation
    
    def _generate_reasoning_steps(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """추론 단계 생성"""
        steps = []
        
        # 입력 분석 단계
        steps.append({
            'step': 1,
            'description': 'Input Analysis',
            'details': f"Analyzed input data: {list(context.get('inputs', {}).keys())}",
            'data': context.get('inputs', {})
        })
        
        # 규칙/모델 적용 단계
        if context.get('rules_applied'):
            steps.append({
                'step': 2,
                'description': 'Rule Application',
                'details': f"Applied rules: {context['rules_applied']}",
                'data': {'rules': context['rules_applied']}
            })
        
        if context.get('model_prediction'):
            steps.append({
                'step': 2,
                'description': 'Model Prediction',
                'details': f"Model output: {context['model_prediction']}",
                'data': {'prediction': context['model_prediction']}
            })
        
        # 결론 도출 단계
        steps.append({
            'step': len(steps) + 1,
            'description': 'Decision Formation',
            'details': f"Final decision: {context.get('output')}",
            'data': {'decision': context.get('output')}
        })
        
        return steps
    
    def _generate_human_explanation(self, context: Dict[str, Any]) -> str:
        """인간이 이해하기 쉬운 설명 생성"""
        decision_type = context.get('type', 'unknown')
        
        if decision_type in self.explanation_templates:
            template = self.explanation_templates[decision_type]
            
            try:
                return template.format(**context)
            except KeyError:
                # 템플릿에 필요한 키가 없는 경우 기본 설명
                return f"Agent made decision of type '{decision_type}' based on available data."
        
        return f"Decision made using {decision_type} approach. Output: {context.get('output', 'Unknown')}"

    def generate_trust_report(self, agent_id: str, time_window_hours: int = 24) -> Dict[str, Any]:
        """신뢰성 보고서 생성"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        relevant_decisions = [
            d for d in self.decision_history
            if d['agent_id'] == agent_id and d['timestamp'] >= cutoff_time
        ]
        
        if not relevant_decisions:
            return {'message': 'No decisions found in the specified time window'}
        
        # 신뢰성 메트릭 계산
        avg_confidence = statistics.mean(d['confidence_level'] for d in relevant_decisions)
        decision_types = [d['decision_type'] for d in relevant_decisions]
        type_distribution = {dt: decision_types.count(dt) for dt in set(decision_types)}
        
        # 일관성 분석
        consistency_score = self._calculate_consistency(relevant_decisions)
        
        return {
            'agent_id': agent_id,
            'time_window_hours': time_window_hours,
            'total_decisions': len(relevant_decisions),
            'average_confidence': avg_confidence,
            'decision_type_distribution': type_distribution,
            'consistency_score': consistency_score,
            'recent_decisions': relevant_decisions[-5:]  # 최근 5개
        }
    
    def _calculate_consistency(self, decisions: List[Dict]) -> float:
        """의사결정 일관성 점수 계산"""
        if len(decisions) < 2:
            return 1.0
        
        # 유사한 입력에 대한 유사한 출력 비율 계산
        consistent_pairs = 0
        total_pairs = 0
        
        for i in range(len(decisions)):
            for j in range(i + 1, len(decisions)):
                decision1, decision2 = decisions[i], decisions[j]
                
                # 입력 유사성 확인 (간단한 구현)
                if self._are_inputs_similar(decision1, decision2):
                    total_pairs += 1
                    if self._are_outputs_consistent(decision1, decision2):
                        consistent_pairs += 1
        
        return consistent_pairs / total_pairs if total_pairs > 0 else 1.0
    
    def _are_inputs_similar(self, decision1: Dict, decision2: Dict) -> bool:
        """입력 유사성 확인"""
        inputs1 = decision1.get('input_data', {})
        inputs2 = decision2.get('input_data', {})
        
        # 간단한 유사성 체크 (실제로는 더 정교한 방법 사용)
        common_keys = set(inputs1.keys()) & set(inputs2.keys())
        if not common_keys:
            return False
        
        similarity_count = 0
        for key in common_keys:
            if inputs1[key] == inputs2[key]:
                similarity_count += 1
        
        return similarity_count / len(common_keys) > 0.7
    
    def _are_outputs_consistent(self, decision1: Dict, decision2: Dict) -> bool:
        """출력 일관성 확인"""
        output1 = decision1.get('output')
        output2 = decision2.get('output')
        
        # 간단한 일관성 체크
        return output1 == output2
