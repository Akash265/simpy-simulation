import simpy
from config import config
from storage import AdvancedStorage  # Use the AdvancedStorage class

class ResourceHandler:
    def __init__(self, env, num_forklifts, num_unloading_docks, num_loading_docks, num_assembly_areas):
        """
        Initialize the ResourceHandler.
        
        Parameters:
        - env: The simulation environment.
        - num_forklifts: Number of forklifts available in the warehouse.
        - num_unloading_docks: Number of unloading docks available.
        - num_loading_docks: Number of loading docks available.
        """
        self.env = env
        
        self.forklifts = simpy.PriorityResource(env, capacity=num_forklifts)
        self.unloading_docks = simpy.Resource(env, capacity=num_unloading_docks)
        self.loading_docks = simpy.Resource(env, capacity=num_loading_docks)
        self.assembly_areas = simpy.Resource(env, capacity=num_assembly_areas)

        # Add advanced storage system
        self.storage = AdvancedStorage(
            num_aisles=config["storage_aisles"],
            slots_per_aisle=config["storage_slots_per_aisle"],
            levels_per_slot=config["storage_levels_per_slot"],
            pallet_types=config["pallet_types"]
        )
        self.storage.initial_storage(config["initial_storage"])
        
        # Metrics
        self.forklift_usage_time = 0
        self.unloading_dock_usage_time = 0
        self.loading_dock_usage_time = 0

    def use_forklift(self, duration):
        """Simulate the usage of a forklift and track its utilization."""
        start_time = self.env.now
        yield self.env.timeout(duration)
        self.forklift_usage_time += self.env.now - start_time

    def use_unloading_dock(self, duration):
        """Simulate the usage of an unloading dock and track its utilization."""
        start_time = self.env.now
        yield self.env.timeout(duration)
        self.unloading_dock_usage_time += self.env.now - start_time

    def use_loading_dock(self, duration):
        """Simulate the usage of a loading dock and track its utilization."""
        start_time = self.env.now
        yield self.env.timeout(duration)
        self.loading_dock_usage_time += self.env.now - start_time

    def get_forklift_utilization(self, total_time):
        """Calculate forklift utilization as a percentage."""
        return (self.forklift_usage_time / (total_time * self.forklifts.capacity)) * 100

    def get_unloading_dock_utilization(self, total_time):
        """Calculate unloading dock utilization as a percentage."""
        return (self.unloading_dock_usage_time / (total_time * self.unloading_docks.capacity)) * 100

    def get_loading_dock_utilization(self, total_time):
        """Calculate loading dock utilization as a percentage."""
        return (self.loading_dock_usage_time / (total_time * self.loading_docks.capacity)) * 100

    def store_item(self, pallet):
        """
        Assign a storage location for a pallet based on its type.
        
        Parameters:
        - pallet: A pallet object with attributes such as pallet_type and pallet_id.
        
        Returns:
        - Location (aisle, slot, level) where the pallet is stored.
        """
        try:
            location = self.storage.assign_storage_location(
                pallet_type=pallet.pallet_type,
                pallet_id=pallet.pallet_id,
            )
            print(f"Stored pallet {pallet.pallet_id} ({pallet.pallet_type}) at {location}.")
            return location
        except ValueError as e:
            print(f"Failed to store pallet {pallet.pallet_id}: {e}")
            return None

    def retrieve_item(self, pallet_id):
        """
        Retrieve an item from storage based on its pallet ID.
        
        Parameters:
        - pallet_id: The unique identifier for the pallet to retrieve.
        
        Returns:
        - Pallet object and its location in the storage.
        """
        try:
            location = self.storage.retrieve_pallet(pallet_id)
            print(f"Retrieved pallet {pallet_id} from location {location}.")
            return location
        except ValueError as e:
            print(f"Failed to retrieve pallet {pallet_id}: {e}")
            return None

    def get_storage_utilization(self):
        """
        Retrieve the storage utilization percentage.
        
        Returns:
        - Percentage of storage capacity currently filled.
        """
        return self.storage.get_storage_utilization()
    
    
    def assign_assembly_area_us(self):
        """
        Assign an available assembly area for order processing.

        Returns:
        - AssemblyArea: Assigned area or None if all are occupied.
        """
        for area in self.assembly_areas:
            if not area.is_occupied:
                area.is_occupied = True
                return area
        return None

    def release_assembly_area(self, area):
        """
        Release an occupied assembly area.

        Parameters:
        - area: The assembly area to be released.
        """
        area.is_occupied = False
