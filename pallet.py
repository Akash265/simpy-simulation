class Pallet:
    def __init__(self, pallet_id, pallet_type="Regular"):
        """Initialize a pallet.
        
        Parameters:
        - pallet_id: A unique identifier for the pallet.
        - pallet_type: The type of the pallet (e.g., Regular, Fragile, Heavy). Default is "Regular".
        """
        self.pallet_id = pallet_id
        self.pallet_type = pallet_type
        self.location = None
        self.created_time = None  # Time when the pallet is created
        self.unloaded_time = None  # Time when the pallet is unloaded at the dock
        self.stored_time = None  # Time when the pallet is stored in the main storage

    def record_creation_time(self, time):
        """Record the creation time of the pallet."""
        self.created_time = time

    def record_unloaded_time(self, time):
        """Record the time when the pallet is unloaded at the dock."""
        self.unloaded_time = time

    def record_stored_time(self, time):
        """Record the time when the pallet is stored in the main storage."""
        self.stored_time = time

    def calculate_time_in_dock(self):
        """Calculate the time the pallet spent in the dock's storage.
        
        Returns:
        - float: Time spent in the dock or None if not applicable.
        """
        if self.unloaded_time and self.stored_time:
            return self.stored_time - self.unloaded_time
        return None

    def __str__(self):
        """String representation of the pallet."""
        return f"Pallet {self.pallet_id} ({self.pallet_type})"

