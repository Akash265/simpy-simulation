class Dock:
    def __init__(self, dock_id, location):
        """Initialize an unloading/loading dock.
        
        Parameters:
        - dock_id: A unique identifier for the dock.
        """
        self.dock_id = dock_id
        self.pallet_storage = []  # Temporary storage area for pallets in the dock
        self.is_occupied = False
        self.location = location
    
    def store_pallet(self, pallet):
        """Store a pallet in the dock's storage area.
        
        Parameters:
        - pallet: The pallet being 
        .
        """
        self.pallet_storage.append(pallet)
        pallet.location = self.location
        #print(f"Pallet {pallet.pallet_id} stored at Dock {self.dock_id}.")
    
    def get_all_pallets(self):
        """Retrieve all pallets from the dock's storage area.
        
        Returns:
        - List[Pallet]: All pallets in the dock's storage.
        """
        pallets = self.pallet_storage
        self.pallet_storage = []  # Clear the storage after retrieval
        return pallets
    
    def has_pallets(self):
        """Check if the dock has pallets in its storage area.
        
        Returns:
        - bool: True if there are pallets in the dock, otherwise False.
        """
        return len(self.pallet_storage) > 0


    def __str__(self):
        """String representation of the dock."""
        return f"Dock {self.dock_id} with {len(self.pallet_storage)} pallets in storage"
