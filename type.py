class Type:
    def __init__(self, type_id, type_name):
        """Initialize a Type object.

        Parameters:
        - type_id: Unique identifier for the type
        - type_name: The name of the type (e.g., 'Pallet', 'Truck', 'Order')
        """
        self.type_id = type_id
        self.type_name = type_name

    def __repr__(self):
        """Return a string representation of the Type object."""
        return f"Type({self.type_id}, '{self.type_name}')"
