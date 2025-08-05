# 예시: 에이전트 상태 백업 시스템
import pickle
import json
import gzip
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, List

class AgentStateManager:
    def __init__(self, agent_id: str, backup_directory: str = "./backups"):
        self.agent_id = agent_id
        self.backup_directory = backup_directory
        self.state_history = []
        self.max_backups = 10
        
        # 백업 디렉토리 생성
        os.makedirs(backup_directory, exist_ok=True)
    
    def save_state(self, state: Dict[str, Any]) -> str:
        """에이전트 상태 저장"""
        timestamp = datetime.now().isoformat()
        backup_id = hashlib.md5(f"{self.agent_id}_{timestamp}".encode()).hexdigest()
        
        # 상태 데이터 준비
        state_data = {
            'agent_id': self.agent_id,
            'timestamp': timestamp,
            'backup_id': backup_id,
            'state': state,
            'checksum': self._calculate_checksum(state)
        }
        
        # 압축하여 저장
        filename = f"{self.backup_directory}/state_{self.agent_id}_{backup_id}.backup"
        with gzip.open(filename, 'wb') as f:
            pickle.dump(state_data, f)
        
        # 히스토리 관리
        self.state_history.append({
            'backup_id': backup_id,
            'timestamp': timestamp,
            'filename': filename
        })
        
        # 오래된 백업 삭제
        self._cleanup_old_backups()
        
        return backup_id
    
    def restore_state(self, backup_id: str = None) -> Dict[str, Any]:
        """에이전트 상태 복원"""
        if backup_id is None:
            # 가장 최근 백업 사용
            if not self.state_history:
                raise ValueError("No backups available")
            backup_id = self.state_history[-1]['backup_id']
        
        # 백업 파일 찾기
        backup_info = next(
            (b for b in self.state_history if b['backup_id'] == backup_id),
            None
        )
        
        if not backup_info:
            raise ValueError(f"Backup {backup_id} not found")
        
        # 백업 파일 로드
        try:
            with gzip.open(backup_info['filename'], 'rb') as f:
                state_data = pickle.load(f)
            
            # 체크섬 검증
            if not self._verify_checksum(state_data['state'], state_data['checksum']):
                raise ValueError("Backup file is corrupted")
            
            return state_data['state']
            
        except Exception as e:
            raise ValueError(f"Failed to restore backup: {e}")
    
    def _calculate_checksum(self, state: Dict[str, Any]) -> str:
        """상태 데이터의 체크섬 계산"""
        state_json = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def _verify_checksum(self, state: Dict[str, Any], expected_checksum: str) -> bool:
        """체크섬 검증"""
        actual_checksum = self._calculate_checksum(state)
        return actual_checksum == expected_checksum
    def _cleanup_old_backups(self):
        """오래된 백업 정리"""
        if len(self.state_history) > self.max_backups:
            # 가장 오래된 백업 삭제
            oldest_backup = self.state_history.pop(0)
            try:
                os.remove(oldest_backup['filename'])
            except FileNotFoundError:
                pass
    
    def get_backup_history(self) -> List[Dict]:
        """백업 히스토리 조회"""
        return self.state_history.copy()

class DistributedBackupManager:
    def __init__(self, replication_factor: int = 3):
        self.replication_factor = replication_factor
        self.backup_nodes = []
        self.node_health = {}
    
    def add_backup_node(self, node_id: str, endpoint: str):
        """백업 노드 추가"""
        self.backup_nodes.append({
            'node_id': node_id,
            'endpoint': endpoint,
            'last_sync': None
        })
        self.node_health[node_id] = True
    
    async def replicate_state(self, agent_id: str, state: Dict[str, Any]):
        """상태를 여러 노드에 복제"""
        healthy_nodes = [
            node for node in self.backup_nodes 
            if self.node_health.get(node['node_id'], False)
        ]
        
        if len(healthy_nodes) < self.replication_factor:
            raise Exception("Insufficient healthy backup nodes")
        
        # 복제할 노드 선택
        selected_nodes = healthy_nodes[:self.replication_factor]
        
        replication_tasks = []
        for node in selected_nodes:
            task = self._replicate_to_node(node, agent_id, state)
            replication_tasks.append(task)
        
        # 병렬 복제 실행
        results = await asyncio.gather(*replication_tasks, return_exceptions=True)
        
        # 성공한 복제 수 확인
        successful_replications = sum(1 for r in results if not isinstance(r, Exception))
        
        if successful_replications < (self.replication_factor // 2 + 1):
            raise Exception("Failed to achieve minimum replication threshold")
    
    async def _replicate_to_node(self, node: Dict, agent_id: str, state: Dict[str, Any]):
        """개별 노드로 복제"""
        try:
            # HTTP 요청으로 백업 노드에 상태 전송
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{node['endpoint']}/backup",
                    json={'agent_id': agent_id, 'state': state}
                ) as response:
                    if response.status == 200:
                        node['last_sync'] = time.time()
                        return True
                    else:
                        raise Exception(f"Backup failed with status {response.status}")
                        
        except Exception as e:
            self.node_health[node['node_id']] = False
            raise e