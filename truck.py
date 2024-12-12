from pallet import Pallet
from config import config
from numpy.random import choice
 

 

class UnloadingTruck:
    def __init__(self, env, truck_id, capacity):
        """Initialize an unloading truck.
        
        Parameters:
        - env: The simulation environment.
        - truck_id: A unique identifier for the truck.
        - capacity: Number of pallets the truck can carry.
        """
        self.env = env
        self.truck_id = truck_id
        self.capacity = capacity
        self.pallets = [Pallet(f"Truck-{truck_id}-Pallet-{i}",choice(config["pallet_types"], 1, p=config['pallet_probs'])[0]) for i in range(capacity)]
    
    def unload(self):
        """Simulate unloading a pallet from the truck.
        
        Returns:
        - Pallet: The pallet being unloaded.
        """
        if self.pallets:
            return self.pallets.pop(0)
        else:
            raise ValueError(f"Truck {self.truck_id} is empty and has no pallets to unload.")

    def is_empty(self):
        """Check if the truck is empty.
        
        Returns:
        - bool: True if the truck has no pallets, otherwise False.
        """
        return len(self.pallets) == 0

    def __str__(self):
        """String representation of the truck."""
        return f"Truck {self.truck_id} with {len(self.pallets)} pallets remaining"
