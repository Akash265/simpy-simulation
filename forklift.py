class Forklift:
    def __init__(self, env, forklift_id, speed_xy, speed_z):
        self.env = env
        self.id = forklift_id  # Add ID to Forklift
        self.speed_xy = speed_xy  # Speed in X and Y direction (units/minute)
        self.speed_z = speed_z  # Speed in Z direction (levels/minute)
        self.available = True  # Track if the forklift is available

    def __str__(self):
        return f"Forklift-{self.id} (Speed XY: {self.speed_xy}, Speed Z: {self.speed_z})"
