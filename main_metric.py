import simpy
import random
from config import config
from truck import UnloadingTruck
from dock import Dock
from resource_handler import ResourceHandler
from order import Order
from assembly_area import AssemblyArea
import numpy as np
from loading_truck import LoadingTruck

np.set_printoptions(legacy='1.25')

t_unload_pallat = 0.1  # minutes
t_check_inventory = 1  # minutes

# Global lists to store metrics
truck_unloading_times = []
truck_loading_times = []
order_assembling_waiting_times = []
order_assembling_times = []
order_loading_waiting_times = []
pallet_times = []
pallet_pickup_times = []

def truck_arrival(env, resource_handler, unloading_docks, dock_list, truck_id):
    """Simulate the arrival and unloading process of a truck."""
    truck = UnloadingTruck(env, truck_id, config["truck_capacity"])
    print(f"[{round(env.now,2)}] Truck {truck_id} arrived with {truck.capacity} pallets.")
    arrival_time = env.now

    # Request an unloading dock
    with unloading_docks.request() as dock_request:
        yield dock_request

        # Find the first available dock
        available_dock = next((dock for dock in dock_list if not dock.is_occupied), None)
        if available_dock is None:
            raise RuntimeError("No available dock despite dock request being granted.")

        available_dock.is_occupied = True  # Mark the dock as occupied
        print(f"[{round(env.now,2)}] Truck {truck_id} assigned to Dock {available_dock.dock_id}.")

        # Simulate truck unloading and moving pallets to storage in parallel
        start_unloading_time = env.now
        forklift_processes = []
        for _ in range(config["forklifts_per_unload_dock"]):
            forklift_processes.append(env.process(handle_unloading_forklift(env, truck, available_dock, resource_handler)))

        # Wait for all forklift processes to finish
        yield simpy.events.AllOf(env, forklift_processes)

        unloading_duration = env.now - start_unloading_time
        resource_handler.unloading_dock_usage_time += unloading_duration
        print(f"[{round(env.now,2)}] Truck {truck_id} finished unloading and is leaving.")

        # Record truck unloading time
        truck_unloading_times.append(unloading_duration)

        # Mark the dock as free
        available_dock.is_occupied = False
        print(f"[{round(env.now,2)}] Dock {available_dock.dock_id} is now free.")

def handle_unloading_forklift(env, truck, dock, resource_handler):
    """Handle unloading of pallets using one forklift."""
    while not truck.is_empty():
        with resource_handler.forklifts.request() as forklift_request:  # Request from unloading forklifts
            yield forklift_request
            # Unload a pallet from the truck
            yield env.process(resource_handler.use_forklift(t_unload_pallat))  # Time to unload a pallet
            pallet = truck.unload()  # Unload a pallet from the truck
            dock.store_pallet(pallet)
            print(f"[{round(env.now,2)}] {pallet.pallet_id} ({pallet.pallet_type}) unloaded at Dock {dock.dock_id}.")
    
def handle_forklift(env, truck, dock, resource_handler):
    """Handle forklift tasks for unloading or moving pallets to storage."""
    forklift_speed_xy = config["forklift_speed_xy"]  # Speed for X and Y in units/minute
    lever_speed_z = config["lever_speed_z"]  # Speed for Z direction in levels/minute
    while True:
        with resource_handler.forklifts.request() as forklift_request:
            yield forklift_request

            # Move pallets to storage if dock has pallets
            if dock.has_pallets():
                pallet = dock.pallet_storage.pop(0)
                # Get target storage location
                storage, location = resource_handler.storage.assign_storage_location(pallet)

                s_x, s_y, z = location  # Target aisle, slot, and level
                d_x, d_y, _ = dock.location
                # Calculate travel time for X, Y, and Z
                x, y = abs(s_x - d_x), abs(s_y - d_y)
                travel_time_x = x / forklift_speed_xy
                travel_time_y = y / forklift_speed_xy
                travel_time_z = z / lever_speed_z

                t_store_pallat = (travel_time_x + travel_time_y + travel_time_z)

                # Store the pallet
                try:
                    print(f"[{round(env.now,2)}] Using Forklift to transport {pallet.pallet_id} ({pallet.pallet_type}) to storage {location} ")
                    yield env.process(resource_handler.use_forklift(t_store_pallat))
                    pallet.location = location
                    aisle, slot, level = storage
                    resource_handler.storage.storage[aisle][slot][level] = pallet
                    print(f"[{round(env.now,2)}] {pallet.pallet_id} ({pallet.pallet_type}) stored at {storage}.")
                    yield env.process(resource_handler.use_forklift(t_store_pallat))
                except ValueError as e:
                    print(f"[{round(env.now,2)}] Storage full: {e}. Returning pallet to dock.")
                    dock.pallet_storage.insert(0, pallet)  # Return pallet to dock
            else:
                break

def generate_truck_arrivals(env, resource_handler, unloading_docks, dock_list):
    """Generate trucks arriving for unloading."""
    truck_id = 0
    while True:
        yield env.timeout(60 / config["unloading_trucks_per_hour"])  # Trucks arrive at regular intervals
        truck_id += 1
        env.process(truck_arrival(env, resource_handler, unloading_docks, dock_list, truck_id))

def generate_orders(env, resource_handler, assembly_area_list):
    order_id = 0
    order_inventory = {}
    for pallet_type in config["pallet_types"]:
        order_inventory[pallet_type] = []
    while True:
        yield env.timeout(60 / config["orders_per_hour"])  # Orders arrive at regular intervals
        order_id += 1
        total_order_size = random.randint(config["minimum_order_size"], config["maximum_order_size"])
        full_order = np.random.choice(config["pallet_types"], total_order_size, p=config['pallet_probs']).tolist()
        pallets_required = {
            pallet_type: count
            for pallet_type, count in (
                (pallet_type, full_order.count(pallet_type))
                for pallet_type in config["pallet_types"]
            )
        }
        order = Order(order_id, pallets_required)
        for pallet_type, required_quantity in order.pallets_required.items():
            if len(order_inventory[pallet_type]) > 0 and required_quantity > 0:
                if order_inventory[pallet_type][-1] > 0:
                    order_inventory[pallet_type].append(order_inventory[pallet_type][-1] + required_quantity)
                else:
                    last_non_quantity = next((x for x in reversed(order_inventory[pallet_type]) if x != 0), None)
                    if last_non_quantity:
                        order_inventory[pallet_type].append(last_non_quantity + required_quantity)
                    else:
                        order_inventory[pallet_type].append(required_quantity)
            else:
                order_inventory[pallet_type].append(required_quantity)
        print(f"[{round(env.now,2)}] Generated {order}.")
        env.process(assemble_order(env, resource_handler, order, assembly_area_list, order_inventory))

def assemble_order(env, resource_handler, order, assembly_area_list, order_inventory):
    """Simulate the assembly of an order."""
    order_id = order.order_id
    print(f"[{round(env.now,2)}] Starting to process Order {order_id}.")
    order_start_time = env.now

    while True:
        missing_pallets = {}
        for pallet_type, required_quantities in order_inventory.items():
            available_quantity = resource_handler.storage.get_available_quantity(pallet_type)
            idx = order_id - 1
            required_quantity = required_quantities[idx]
            if available_quantity < required_quantity:
                missing_pallets[pallet_type] = required_quantity - available_quantity

        if not missing_pallets:
            print(f"[{round(env.now,2)}] All pallets for Order {order.order_id} are available. Starting assembly.")
            assembly_start_time = env.now
            order_assembling_waiting_times.append(assembly_start_time - order_start_time)

            while True:
                # Find the first available dock
                with resource_handler.assembly_areas.request() as area_request:
                    yield area_request  # Reserve the area

                    available_assembly_area = next((assembly_area for assembly_area in assembly_area_list if not assembly_area.is_occupied), None)

                    if available_assembly_area is None:
                        raise RuntimeError("No available assemble area despite assemble area request being granted.")

                    available_assembly_area.is_occupied = True  # Mark the dock as occupied
                    area_id = available_assembly_area.area_id
                    print(f"[{round(env.now,2)}] Order {order_id} assigned to Assemble Area {area_id}.")

                    # Perform assembly
                    yield env.process(perform_assembly(env, resource_handler, order, available_assembly_area))
                    for pallet_type, required_quantities in order_inventory.items():
                        order_inventory[pallet_type][idx] -= order_inventory[pallet_type][idx]

                    if available_assembly_area.check_available_storage(config["maximum_order_size"]):
                        available_assembly_area.is_occupied = True
                    else:
                        available_assembly_area.is_occupied = False
                    print(f"[{round(env.now,2)}] Order {order_id} released Assembly Area {area_id}.")
                    available_assembly_area.num_orders += 1
                    available_assembly_area.orders.append(order)
                    assembly_end_time = env.now
                    order_assembling_times.append(assembly_end_time - assembly_start_time)
                    return

                # If no assembly area is available, wait and retry
                print(f"[{round(env.now,2)}] Order {order_id} is waiting for an available assembly area.")
                yield env.timeout(1)  # Check every 1 time unit
        else:
            print(f"[{round(env.now,2)}] Order {order_id} is waiting for missing pallets: {missing_pallets}.")
            yield env.timeout(2)  # Check inventory every 2 minutes

def perform_assembly(env, resource_handler, order, assembly_area):
    pallets_to_handle = order.pallets_required.copy()

    total_pallets_to_handle = sum(pallets_to_handle.values())
    while any(pallets_to_handle.values()):
        forklifts_available = min(config["forklifts_per_order_assembly"], resource_handler.forklifts.capacity)
        assembly_processes = []

        for _ in range(forklifts_available):
            with resource_handler.forklifts.request() as forklift_request:
                yield forklift_request

                # Assign work to the forklift
                pallet_type = next((p for p, qty in pallets_to_handle.items() if qty > 0), None)
                if pallet_type:
                    pallets_to_handle[pallet_type] -= 1
                    pallet_location = resource_handler.storage.get_item(pallet_type)
                    s_x, s_y, z = pallet_location  # Source aisle, slot, and level
                    a_x, a_y, _ = assembly_area.location
                    # Calculate travel times
                    travel_time_x = abs(s_x - a_x) / config["forklift_speed_xy"]
                    travel_time_y = abs(s_y - a_y) / config["forklift_speed_xy"]
                    travel_time_z = z / config["lever_speed_z"]

                    t_assemble = (travel_time_x + travel_time_y + travel_time_z) * 2
                    # Simulate assembly time
                    assembly_processes.append(env.process(resource_handler.use_forklift(t_assemble)))

        # Wait for all forklifts to complete this batch
        yield simpy.AllOf(env, assembly_processes)
    assembly_area.current_storage += total_pallets_to_handle

    print(f"[{round(env.now,2)}] Assembly for Order {order.order_id} completed.")

def generate_loading_trucks(env, resource_handler, assembly_area_list, dock_list):
    """Generate loading trucks arriving at the facility."""
    truck_id = 0
    while True:
        yield env.timeout(60 / config["loading_trucks_per_hour"])  # Trucks arrive at regular intervals
        truck_id += 1
        env.process(loading_truck_arrival(env, resource_handler, assembly_area_list, dock_list, truck_id))

def loading_truck_arrival(env, resource_handler, assembly_area_list, dock_list, truck_id):
    """Simulate the arrival and loading process of a truck."""
    truck = LoadingTruck(env, truck_id, config["truck_capacity"])
    print(f"[{round(env.now,2)}] Loading Truck {truck_id} arrived.")

    # Request a loading dock
    with resource_handler.loading_docks.request() as dock_request:
        yield dock_request

        # Find the first available dock
        available_dock = next((dock for dock in dock_list if not dock.is_occupied), None)
        if available_dock is None:
            raise RuntimeError("No available dock despite dock request being granted.")

        available_dock.is_occupied = True
        print(f"[{round(env.now,2)}] Loading Truck {truck_id} assigned to Dock {available_dock.dock_id}.")

        assembly_area = assembly_area_list[available_dock.dock_id - 1]
        # Wait for order assembly if not ready
        order_ready = assembly_area.num_orders > 0
        while not order_ready:
            print(f"[{round(env.now,2)}] Loading Truck {truck_id} is waiting for an assembled order.")
            loading_start_wait_time = env.now
            yield env.timeout(1)  # Check every 1 time unit
            order_ready = assembly_area.num_orders > 0

        pallets_to_load = None
        # Transfer order from assembly area to the loading dock
        for idx in range(len(assembly_area.orders)):
            if not assembly_area.orders[idx].shipped:
                pallets_to_load = sum(assembly_area.orders[idx].pallets_required.values())
                break
        
        assembly_area_list[available_dock.dock_id - 1].num_orders -= 1
        a_x, a_y, _ = assembly_area.location  # Source aisle, slot, and level
        d_x, d_y, _ = available_dock.location
        # Calculate travel times
        travel_time_x = abs(d_x - a_x) / config["forklift_speed_xy"]
        travel_time_y = abs(d_y - a_y) / config["forklift_speed_xy"]
        t_transfer = (travel_time_x + travel_time_y) * pallets_to_load * 2
        yield env.process(resource_handler.use_forklift(t_transfer))
        print(f"[{round(env.now,2)}] Transferred {pallets_to_load} pallets from Assembly Area {assembly_area.area_id} to Dock {available_dock.dock_id}.")
        assembly_area.current_storage -= pallets_to_load
        if not assembly_area.check_available_storage(config["maximum_order_size"]):
            assembly_area.is_occupied = False
        # Load the truck
        loading_start_time = env.now
        yield env.process(handle_loading_forklift(env, truck, available_dock, pallets_to_load, resource_handler))

        print(f"[{round(env.now,2)}] Loading Truck {truck_id} finished loading and is leaving.")
        truck_loading_times.append(env.now - loading_start_time)
        available_dock.is_occupied = False
        assembly_area.orders[idx].shipped = True
        print(f"[{round(env.now,2)}] Loading Dock {available_dock.dock_id} is now free.")

def handle_loading_forklift(env, truck, dock, pallets_to_load, resource_handler):
    """Handle loading of pallets onto a truck using one forklift."""
    with resource_handler.forklifts.request() as forklift_request:
        yield forklift_request
        # Time to load pallets
        load_time = pallets_to_load * t_unload_pallat  # Assuming same time as unloading
        print(f"[{round(env.now,2)}] Using Forklift to load {pallets_to_load} pallets onto Truck.")
        yield env.process(resource_handler.use_forklift(load_time))
        loaded_pallets = truck.load(pallets_to_load)
        print(f"[{round(env.now,2)}] Loaded {loaded_pallets} pallets onto Truck.")

def main():
    """Main function to run the simulation."""
    # Initialize simulation environment
    env = simpy.Environment()

    unloading_dock_start_y = 4
    width_unloading_dock = 6
    unloading_dock_end_y = unloading_dock_start_y + width_unloading_dock * config["num_unloading_docks"]
    unloading_dock_x = 2  # The x-coordinate for unloading docks (parallel to aisles)

    assembly_area_start_x = 6
    width_assembly_area = 9
    assembly_area_end_x = assembly_area_start_x + width_assembly_area * config["num_assembly_area"]
    assembly_area_y = -4

    loading_dock_start_x = 6
    width_loading_dock = 9
    loading_dock_end_x = loading_dock_start_x + width_loading_dock * config["num_loading_docks"]
    loading_dock_y = -8

    # Create unloading docks
    dock_list = [Dock(dock_id, (unloading_dock_x, round(y, 2), 0)) for dock_id, y in
                 zip(range(1, config["num_unloading_docks"] + 1),
                     np.arange(unloading_dock_start_y, unloading_dock_end_y, width_unloading_dock))]
    assembly_area_list = [AssemblyArea(assembly_area_id, (round(x, 2), assembly_area_y, 0), config["assembly_area_capacity"])
                          for assembly_area_id, x in
                          zip(range(1, config["num_assembly_area"] + 1),
                              np.arange(assembly_area_start_x, assembly_area_end_x, width_assembly_area))]
    loading_dock_list = [Dock(loading_dock_id, (round(x, 2), loading_dock_y, 0)) for loading_dock_id, x in
                         zip(range(1, config["num_loading_docks"] + 1),
                             np.arange(loading_dock_start_x, loading_dock_end_x, width_loading_dock))]
    # Initialize ResourceHandler
    resource_handler = ResourceHandler(
        env,
        num_forklifts=config["forklifts"],
        num_unloading_docks=config["num_unloading_docks"],
        num_loading_docks=config["num_loading_docks"],
        num_assembly_areas=config["num_assembly_area"]
    )
    # Start truck arrival process
    env.process(generate_truck_arrivals(env, resource_handler, resource_handler.unloading_docks, dock_list))
    env.process(generate_orders(env, resource_handler, assembly_area_list))
    env.process(generate_loading_trucks(env, resource_handler, assembly_area_list, loading_dock_list))

    # Run the simulation
    simulation_duration = config["simulation_duration_minutes"]
    env.run(until=simulation_duration)

    # Print utilization metrics
    print("\n=== Simulation Results ===")
    total_time = simulation_duration
    print(f"Forklift Utilization: {resource_handler.get_forklift_utilization(total_time):.2f}%")
    print(f"Unloading Dock Utilization: {resource_handler.get_unloading_dock_utilization(total_time):.2f}%")
    print(f"Loading Dock Utilization: {resource_handler.get_loading_dock_utilization(total_time):.2f}%")
    print(f"Storage Utilization: {resource_handler.get_storage_utilization():.2f}%")

    # Calculate and print other metrics
    if truck_unloading_times:
        print(f"Truck Unloading Mean Time: {np.mean(truck_unloading_times):.2f} minutes")
    else:
        print("No truck unloading times recorded.")

    if truck_loading_times:
        print(f"Truck Loading Mean Time: {np.mean(truck_loading_times):.2f} minutes")
    else:
        print("No truck loading times recorded.")

    if order_assembling_waiting_times:
        print(f"Order Assembling Mean Waiting Time: {np.mean(order_assembling_waiting_times):.2f} minutes")
    else:
        print("No order assembling waiting times recorded.")

    if order_assembling_times:
        print(f"Order Assembling Mean Time: {np.mean(order_assembling_times):.2f} minutes")
    else:
        print("No order assembling times recorded.")

    if order_loading_waiting_times:
        print(f"Order Loading Mean Waiting Time: {np.mean(order_loading_waiting_times):.2f} minutes")
    else:
        print("No order loading waiting times recorded.")

    if pallet_times:
        print(f"Mean Pallet Time: {np.mean(pallet_times):.2f} minutes")
    else:
        print("No pallet times recorded.")

    if pallet_pickup_times:
        print(f"Mean Pallet Pickup Time: {np.mean(pallet_pickup_times):.2f} minutes")
    else:
        print("No pallet pickup times recorded.")

if __name__ == "__main__":
    main()