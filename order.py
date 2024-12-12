import random
class Order:
    def __init__(self, order_id, pallets_required):
        """
        Initialize an order.

        Parameters:
        - order_id: Unique identifier for the order.
        - pallets_required: Dictionary of pallet types and their required quantities.
        """
        self.order_id = order_id
        self.pallets_required = pallets_required  # Dict with pallet types and quantities
        self.assembled = False
        self.shipped = False
        self.remaining_pallets = self._initialize_pallet_queue()

    def _initialize_pallet_queue(self):
        """Create a queue of pallets based on the required quantities."""
        queue = []
        for pallet_type, quantity in self.pallets_required.items():
            queue.extend([pallet_type] * quantity)
        random.shuffle(queue)  # Randomize the order of pallets
        return queue

    def get_next_pallet(self):
        """
        Retrieve the next pallet to process.

        Returns:
        - The next pallet type as a string.
        Raises:
        - ValueError: If no pallets are left to process.
        """
        if not self.remaining_pallets:
            raise ValueError(f"No pallets left to process for Order {self.order_id}.")
        return self.remaining_pallets.pop(0)

    def is_complete(self):
        """
        Check if the order has been fully assembled.

        Returns:
        - True if all pallets have been processed, False otherwise.
        """
        return len(self.remaining_pallets) == 0

    def __str__(self):
        """
        String representation of the order.
        """
        return (f"Order {self.order_id} "
                f"(Remaining Pallets: {len(self.remaining_pallets)}, "
                f"Pallets Required: {self.pallets_required})")
