# Example: Agent Permission Management System
from enum import Enum
from typing import Set, Dict, List
import json
import time

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
        """Assigns a role to an agent."""
        if role_name not in self.roles:
            raise ValueError(f"Role {role_name} does not exist")
        
        if agent_id not in self.agent_roles:
            self.agent_roles[agent_id] = set()
        
        self.agent_roles[agent_id].add(role_name)
        self._log_access_event(agent_id, f"Role {role_name} assigned")
    
    def check_permission(self, agent_id: str, permission: Permission, resource: str = None) -> bool:
        """Checks an agent's permission."""
        if agent_id not in self.agent_roles:
            self._log_access_event(agent_id, f"Permission {permission.value} denied - no roles")
            return False
        
        # Check all roles of the agent
        for role_name in self.agent_roles[agent_id]:
            role = self.roles[role_name]
            if role.has_permission(permission):
                # Check resource-specific permissions
                if resource and not self._check_resource_permission(agent_id, resource, permission):
                    continue
                
                self._log_access_event(agent_id, f"Permission {permission.value} granted")
                return True
        
        self._log_access_event(agent_id, f"Permission {permission.value} denied")
        return False

    def _check_resource_permission(self, agent_id: str, resource: str, permission: Permission) -> bool:
        """Checks resource-specific permissions."""
        if resource in self.resource_permissions:
            required_permissions = self.resource_permissions[resource]
            return permission in required_permissions
        return True  # Default to allow
    
    def set_resource_permissions(self, resource: str, permissions: Set[Permission]):
        """Sets required permissions for a resource."""
        self.resource_permissions[resource] = permissions
    
    def _log_access_event(self, agent_id: str, event: str):
        """Logs an access event."""
        log_entry = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'event': event
        }
        self.audit_log.append(log_entry)
    
    def get_audit_log(self, agent_id: str = None, hours: int = 24) -> List[Dict]:
        """Retrieves the audit log."""
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

# Example Usage
class SecureAgent:
    def __init__(self, agent_id: str, access_manager: AccessControlManager):
        self.agent_id = agent_id
        self.access_manager = access_manager
    
    def read_sensitive_data(self, data_source: str):
        """Reads sensitive data."""
        if not self.access_manager.check_permission(
            self.agent_id, Permission.READ_DATA, data_source
        ):
            raise PermissionError(f"Access denied to {data_source}")
        
        # Data reading logic
        print(f"Agent {self.agent_id} successfully read data from {data_source}.")
        return f"Data from {data_source}"
    
    def execute_system_command(self, command: str):
        """Executes a system command."""
        if not self.access_manager.check_permission(
            self.agent_id, Permission.SYSTEM_ADMIN
        ):
            raise PermissionError("System admin privileges required")
        
        # Command execution logic
        print(f"Agent {self.agent_id} successfully executed command: {command}")
        return f"Executed: {command}"

if __name__ == "__main__":
    access_manager = AccessControlManager()

    # Create agents
    worker_agent = SecureAgent("worker_bee_01", access_manager)
    admin_agent = SecureAgent("admin_ant_01", access_manager)

    # Assign roles
    access_manager.assign_role(worker_agent.agent_id, "worker")
    access_manager.assign_role(admin_agent.agent_id, "admin")

    print("--- RBAC Demo ---")

    # --- Worker Agent Actions ---
    print("\n--- Testing Worker Agent ---")
    try:
        worker_agent.read_sensitive_data("shared_dataset")
    except PermissionError as e:
        print(f"Worker agent action failed as expected: {e}")

    try:
        worker_agent.execute_system_command("reboot")
    except PermissionError as e:
        print(f"Worker agent action failed as expected: {e}")

    # --- Admin Agent Actions ---
    print("\n--- Testing Admin Agent ---")
    try:
        admin_agent.read_sensitive_data("secret_logs")
        admin_agent.execute_system_command("shutdown -h now")
    except PermissionError as e:
        print(f"Admin agent action failed unexpectedly: {e}")

    # --- Resource-specific permissions ---
    print("\n--- Testing Resource-Specific Permissions ---")
    access_manager.set_resource_permissions("confidential_data", {Permission.SYSTEM_ADMIN})

    print("Admin trying to read 'confidential_data' (should fail):")
    try:
        admin_agent.read_sensitive_data("confidential_data")
    except PermissionError as e:
        print(f"Admin agent action failed as expected: {e}")

    # --- Audit Log ---
    print("\n--- Audit Log ---")
    log = access_manager.get_audit_log()
    for entry in log:
        print(f"  - {entry}")