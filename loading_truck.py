class LoadingTruck:
    def __init__(self, env, truck_id, capacity):
        self.env = env
        self.truck_id = truck_id
        self.capacity = capacity  # Capacity in number of pallets
        self.loaded_pallets = 0

    def load(self, pallets):
        """Load pallets into the truck."""
        if self.loaded_pallets + pallets <= self.capacity:
            self.loaded_pallets += pallets
            return pallets
        else:
            loadable_pallets = self.capacity - self.loaded_pallets
            self.loaded_pallets = self.capacity
            return loadable_pallets

    def is_full(self):
        """Check if the truck is fully loaded."""
        return self.loaded_pallets >= self.capacity
