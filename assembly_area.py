class AssemblyArea:
    def __init__(self, area_id, location, capacity):
        """
        Initialize an assembly area for orders.

        Parameters:
        - area_id: A unique identifier for the assembly area.
        - location: (x, y, z) coordinates of the assembly area.
        - capacity: The maximum number of pallets that can be stored in the assembly area.
        """
        self.area_id = area_id
        self.location = location
        self.capacity = capacity
        self.num_orders = 0  # Temporary storage area for assembling orders
        self.current_storage = 0
        self.is_occupied = False
        self.orders = []

    def check_available_storage(self, max_order_size):
        return self.capacity - self.current_storage  <= max_order_size
    def __str__(self):
        """
        String representation of the assembly area.
        """
        return f"Assembly Area {self.area_id} at {self.location} with {len(self.current_storage)}/{self.capacity} pallets."

