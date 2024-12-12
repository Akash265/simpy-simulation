''''
class Config:
    # Forklifts configuration
    FORKLIFTS = (10, 44)  # Range for number of forklifts in the warehouse (10 to 44)

    # Forklifts per unloading dock configuration
    FORKLIFTS_PER_UNLOAD_DOCK = (0, 10)  # Range for forklifts per unloading dock (0 to 10)

    # Forklifts per order assembling configuration
    FORKS_PER_ORDER_ASSEMBLING = (0, 10)  # Range for forklifts per order assembly (0 to 10)

    # Unloading trucks per hour configuration
    UNLOADING_TRUCKS_PER_HOUR = (0, 10)  # Number of unloading trucks arriving per hour (0 to 10)

    # Loading trucks per hour configuration
    LOADING_TRUCKS_PER_HOUR = (1, 10)  # Number of loading trucks departing per hour (1 to 10)

    # Orders per hour configuration
    ORDERS_PER_HOUR = (0, 10)  # Range for number of orders assembled per hour (0 to 10)

    # Truck capacity configuration (pallets that each truck can carry)
    TRUCK_CAPACITY = (10, 30)  # Truck capacity (10 to 30 pallets)

    # Minimum order size configuration (number of pallets required for an order)
    MIN_ORDER_SIZE = (1, 14)  # Minimum order size (1 to 14 pallets)

    # Maximum order size configuration (number of pallets required for an order)
    MAX_ORDER_SIZE = (10, 15)  # Maximum order size (10 to 15 pallets)

    # Storage settings
    STORAGE_CAPACITY = 100  # Total storage capacity (number of pallets it can store)
    
    # Number of storage docks
    STORAGE_DOCKS = (1, 5)  # Range for the number of docks in the storage area (1 to 5)
    
    # Assembly area settings
    ASSEMBLY_AREA_CAPACITY = 50  # Total capacity of the assembly area (number of pallets)
    
    # Time settings
    SIMULATION_TIME = 24 * 60  # Total simulation time in minutes (e.g., 24 hours)
    
    # Pallet types
    PALLET_TYPES = ["Fragile", "Heavy"]  # Types of pallets used in the warehouse

    # Rack system settings
    RACK_SYSTEM_CAPACITY = 100  # Number of pallets that can be stored in the rack system
    
    # Initial filling rate
    INITIAL_FILL_RATE = 0.2  # Rate at which pallets are initially added to the storage area

    # Truck arrival time (in minutes)
    TRUCK_ARRIVAL_TIME = 5  # Time between truck arrivals (in minutes)

    # Forklift utilization target
    FORKLIFT_UTILIZATION_TARGET = 0.75  # 75% forklift utilization target for efficiency

    # Dock utilization target
    DOCK_UTILIZATION_TARGET = 0.75  # 75% dock utilization target for efficiency

    # Performance Metrics
    # These can be used for logging during the simulation
    METRICS = {
        "truck_unloading_mean_time": 0,
        "truck_loading_mean_time": 0,
        "order_assembling_mean_waiting_time": 0,
        "order_assembling_mean_time": 0,
        "order_loading_mean_waiting_time": 0,
        "mean_pallet_time": 0,
        "mean_pallet_pickup_time": 0,
        "forklift_utilization": 0,
        "unloading_docks_utilization": 0,
        "loading_docks_utilization": 0,
        "storage_utilization": 0
    }

    def __init__(self):
        pass
'''
config = {
    # Simulation parameters
    "forklifts": 30,  # Number of forklifts available in the warehouse
    "forklifts_per_unload_dock": 4,  # Number of forklifts allocated per unloading dock
    "forklifts_per_order_assembly": 2,
    "unloading_trucks_per_hour": 6,  # Number of trucks arriving for unloading per hour
    "loading_trucks_per_hour": 4,  # Number of trucks arriving for loading per hour
    "orders_per_hour": 8,  # Number of orders generated per hour
    "truck_capacity_min": 20,  # Truck capacity min (number of pallets per truck)
    "truck_capacity_max": 20,  # Truck capacity max (number of pallets per truck)
    "minimum_order_size": 5,  # Minimum number of pallets per order
    "maximum_order_size": 12,  # Maximum number of pallets per order
    "assembly_area_capacity": 1000,
    "num_assembly_area": 7,
    
    # Dock parameters
    "num_unloading_docks": 5,  # Number of unloading docks available
    "num_loading_docks": 7,  # Number of loading docks available

    # Pallet parameters
    "pallet_types": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"],  # Types of pallets
    "pallet_probs": [0.3, 0.15, 0.15, 0.08, 0.08, 0.08, 0.08, 0.08],
    # Simulation duration
    "simulation_duration_minutes": 1440,  # Simulation duration in minutes (8 hours)
 
    # Existing parameters...
    "storage_aisles": 32,
    "storage_slots_per_aisle": 38,
    "storage_levels_per_slot": 5,
    
    "forklift_speed_xy": 3,
    "lever_speed_z": 5

}




