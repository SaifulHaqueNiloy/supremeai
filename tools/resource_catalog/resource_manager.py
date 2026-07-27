"""Resource manager for resource catalog tools."""

class ResourceManager:
    """Manage resources in the catalog."""
    
    def __init__(self):
        self.resources = {}
    
    async def register_resource(self, resource_id: str, resource_data: dict) -> bool:
        """Register a new resource."""
        self.resources[resource_id] = {
            "id": resource_id,
            "data": resource_data,
            "registered_at": None
        }
        return True
    
    async def get_resource(self, resource_id: str) -> dict:
        """Get a resource by ID."""
        return self.resources.get(resource_id)
    
    async def list_resources(self, filters: dict = None) -> list:
        """List resources with optional filters."""
        return list(self.resources.values())
    
    async def update_resource(self, resource_id: str, resource_data: dict) -> bool:
        """Update a resource."""
        if resource_id in self.resources:
            self.resources[resource_id]["data"].update(resource_data)
            return True
        return False
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource."""
        if resource_id in self.resources:
            del self.resources[resource_id]
            return True
        return False