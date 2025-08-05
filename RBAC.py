# 예시: 에이전트 권한 관리 시스템
from enum import Enum
from typing import Set, Dict, List
import json

class Permission(Enum):
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    EXECUTE_TASK = "execute_task"
    MANAGE_AGENTS = "manage_agents"
    SYSTEM_ADMIN = "system_admin"
    NETWORK_ACCESS = "network_access"

class Role:
    def __init__(self, name: str, permissions: Set[Permission]):
        self.name = name
        self.permissions = permissions
    
    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

class AccessControlManager:
    def __init__(self):
        self.roles = self._initialize_default_roles()
        self.agent_roles: Dict[str, Set[str]] = {}
        self.resource_permissions: Dict[str, Set[Permission]] = {}
        self.audit_log = []
    
    def _initialize_default_roles(self) -> Dict[str, Role]:
        return {
            'worker': Role('worker', {
                Permission.READ_DATA,
                Permission.EXECUTE_TASK
            }),
            'coordinator': Role('coordinator', {
                Permission.READ_DATA,
                Permission.WRITE_DATA,
                Permission.EXECUTE_TASK,
                Permission.MANAGE_AGENTS
            }),
            'admin': Role('admin', {
                Permission.READ_DATA,
                Permission.WRITE_DATA,
                Permission.EXECUTE_TASK,
                Permission.MANAGE_AGENTS,
                Permission.SYSTEM_ADMIN,
                Permission.NETWORK_ACCESS
            })
        }
    
    def assign_role(self, agent_id: str, role_name: str):
        """에이전트에 역할 할당"""
        if role_name not in self.roles:
            raise ValueError(f"Role {role_name} does not exist")
        
        if agent_id not in self.agent_roles:
            self.agent_roles[agent_id] = set()
        
        self.agent_roles[agent_id].add(role_name)
        self._log_access_event(agent_id, f"Role {role_name} assigned")
    
    def check_permission(self, agent_id: str, permission: Permission, resource: str = None) -> bool:
        """에이전트의 권한 확인"""
        if agent_id not in self.agent_roles:
            self._log_access_event(agent_id, f"Permission {permission.value} denied - no roles")
            return False
        
        # 에이전트의 모든 역할 확인
        for role_name in self.agent_roles[agent_id]:
            role = self.roles[role_name]
            if role.has_permission(permission):
                # 리소스별 권한 확인
                if resource and not self._check_resource_permission(agent_id, resource, permission):
                    continue
                
                self._log_access_event(agent_id, f"Permission {permission.value} granted")
                return True
        
        self._log_access_event(agent_id, f"Permission {permission.value} denied")
        return False

    def _check_resource_permission(self, agent_id: str, resource: str, permission: Permission) -> bool:
        """리소스별 세부 권한 확인"""
        if resource in self.resource_permissions:
            required_permissions = self.resource_permissions[resource]
            return permission in required_permissions
        return True  # 기본적으로 허용
    
    def set_resource_permissions(self, resource: str, permissions: Set[Permission]):
        """리소스별 필요 권한 설정"""
        self.resource_permissions[resource] = permissions
    
    def _log_access_event(self, agent_id: str, event: str):
        """접근 이벤트 로깅"""
        log_entry = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'event': event
        }
        self.audit_log.append(log_entry)
    
    def get_audit_log(self, agent_id: str = None, hours: int = 24) -> List[Dict]:
        """감사 로그 조회"""
        cutoff_time = time.time() - (hours * 3600)
        
        filtered_log = [
            entry for entry in self.audit_log
            if entry['timestamp'] >= cutoff_time
        ]
        
        if agent_id:
            filtered_log = [
                entry for entry in filtered_log
                if entry['agent_id'] == agent_id
            ]
        
        return filtered_log

# 사용 예시
class SecureAgent:
    def __init__(self, agent_id: str, access_manager: AccessControlManager):
        self.agent_id = agent_id
        self.access_manager = access_manager
    
    def read_sensitive_data(self, data_source: str):
        """민감한 데이터 읽기"""
        if not self.access_manager.check_permission(
            self.agent_id, Permission.READ_DATA, data_source
        ):
            raise PermissionError(f"Access denied to {data_source}")
        
        # 데이터 읽기 로직
        return f"Data from {data_source}"
    
    def execute_system_command(self, command: str):
        """시스템 명령 실행"""
        if not self.access_manager.check_permission(
            self.agent_id, Permission.SYSTEM_ADMIN
        ):
            raise PermissionError("System admin privileges required")
        
        # 명령 실행 로직
        return f"Executed: {command}"