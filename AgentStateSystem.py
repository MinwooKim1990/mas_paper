# Example: Agent State Backup System
import pickle
import json
import gzip
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, List
import asyncio
import time
import aiohttp

class AgentStateManager:
    """Manages the state of an agent, including saving and restoring backups."""
    def __init__(self, agent_id: str, backup_directory: str = "./backups"):
        self.agent_id = agent_id
        self.backup_directory = backup_directory
        self.state_history = []
        self.max_backups = 10
        
        # Create backup directory
        os.makedirs(backup_directory, exist_ok=True)
    
    def save_state(self, state: Dict[str, Any]) -> str:
        """Saves the agent's state."""
        timestamp = datetime.now().isoformat()
        backup_id = hashlib.md5(f"{self.agent_id}_{timestamp}".encode()).hexdigest()
        
        # Prepare state data
        state_data = {
            'agent_id': self.agent_id,
            'timestamp': timestamp,
            'backup_id': backup_id,
            'state': state,
            'checksum': self._calculate_checksum(state)
        }
        
        # Save with compression
        filename = f"{self.backup_directory}/state_{self.agent_id}_{backup_id}.backup"
        with gzip.open(filename, 'wb') as f:
            pickle.dump(state_data, f)
        
        # Manage history
        self.state_history.append({
            'backup_id': backup_id,
            'timestamp': timestamp,
            'filename': filename
        })
        
        # Clean up old backups
        self._cleanup_old_backups()
        
        return backup_id
    
    def restore_state(self, backup_id: str = None) -> Dict[str, Any]:
        """Restores the agent's state."""
        if backup_id is None:
            # Use the most recent backup
            if not self.state_history:
                raise ValueError("No backups available")
            backup_id = self.state_history[-1]['backup_id']
        
        # Find the backup file
        backup_info = next(
            (b for b in self.state_history if b['backup_id'] == backup_id),
            None
        )
        
        if not backup_info:
            raise ValueError(f"Backup {backup_id} not found")
        
        # Load the backup file
        try:
            with gzip.open(backup_info['filename'], 'rb') as f:
                state_data = pickle.load(f)
            
            # Verify checksum
            if not self._verify_checksum(state_data['state'], state_data['checksum']):
                raise ValueError("Backup file is corrupted")
            
            return state_data['state']
            
        except Exception as e:
            raise ValueError(f"Failed to restore backup: {e}")
    
    def _calculate_checksum(self, state: Dict[str, Any]) -> str:
        """Calculates the checksum of the state data."""
        state_json = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def _verify_checksum(self, state: Dict[str, Any], expected_checksum: str) -> bool:
        """Verifies the checksum."""
        actual_checksum = self._calculate_checksum(state)
        return actual_checksum == expected_checksum

    def _cleanup_old_backups(self):
        """Cleans up old backups."""
        if len(self.state_history) > self.max_backups:
            # Delete the oldest backup
            oldest_backup = self.state_history.pop(0)
            try:
                os.remove(oldest_backup['filename'])
            except FileNotFoundError:
                pass
    
    def get_backup_history(self) -> List[Dict]:
        """Retrieves the backup history."""
        return self.state_history.copy()

class DistributedBackupManager:
    """Manages the distributed backup of agent states."""
    def __init__(self, replication_factor: int = 3):
        self.replication_factor = replication_factor
        self.backup_nodes = []
        self.node_health = {}
    
    def add_backup_node(self, node_id: str, endpoint: str):
        """Adds a backup node."""
        self.backup_nodes.append({
            'node_id': node_id,
            'endpoint': endpoint,
            'last_sync': None
        })
        self.node_health[node_id] = True
    
    async def replicate_state(self, agent_id: str, state: Dict[str, Any]):
        """Replicates the state to multiple nodes."""
        healthy_nodes = [
            node for node in self.backup_nodes 
            if self.node_health.get(node['node_id'], False)
        ]
        
        if len(healthy_nodes) < self.replication_factor:
            raise Exception("Insufficient healthy backup nodes")
        
        # Select nodes to replicate to
        selected_nodes = healthy_nodes[:self.replication_factor]
        
        replication_tasks = []
        for node in selected_nodes:
            task = self._replicate_to_node(node, agent_id, state)
            replication_tasks.append(task)
        
        # Execute replication in parallel
        results = await asyncio.gather(*replication_tasks, return_exceptions=True)
        
        # Check the number of successful replications
        successful_replications = sum(1 for r in results if not isinstance(r, Exception))
        
        if successful_replications < (self.replication_factor // 2 + 1):
            raise Exception("Failed to achieve minimum replication threshold")
    
    async def _replicate_to_node(self, node: Dict, agent_id: str, state: Dict[str, Any]):
        """Replicates to an individual node."""
        try:
            # Send state to backup node via HTTP request
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

if __name__ == '__main__':
    # --- AgentStateManager Demo ---
    print("--- AgentStateManager Demo ---")
    agent_id = "test_agent"
    # Create a temporary directory for backups for the demo
    backup_dir = "temp_backups"
    state_manager = AgentStateManager(agent_id, backup_directory=backup_dir)

    # Save a few states
    initial_state = {"value": 1, "status": "initial"}
    backup_id1 = state_manager.save_state(initial_state)
    print(f"Saved state with backup ID: {backup_id1}")

    time.sleep(1) # ensure timestamp is different

    updated_state = {"value": 2, "status": "updated"}
    backup_id2 = state_manager.save_state(updated_state)
    print(f"Saved state with backup ID: {backup_id2}")

    # Display backup history
    history = state_manager.get_backup_history()
    print(f"Backup history: {history}")

    # Restore the first state
    restored_state = state_manager.restore_state(backup_id1)
    print(f"Restored state from {backup_id1}: {restored_state}")
    assert restored_state == initial_state

    # Restore the latest state
    latest_restored_state = state_manager.restore_state()
    print(f"Restored latest state: {latest_restored_state}")
    assert latest_restored_state == updated_state

    # Clean up the temporary backup directory
    import shutil
    shutil.rmtree(backup_dir)
    print(f"Cleaned up temporary backup directory: {backup_dir}")

    # --- DistributedBackupManager Demo ---
    print("\n--- DistributedBackupManager Demo ---")
    print("Demonstration for DistributedBackupManager is omitted because it requires running mock servers.")
    print("The code is intended to be used in a larger application with a running asyncio event loop.")