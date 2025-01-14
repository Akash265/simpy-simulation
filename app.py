from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import simpy
import numpy as np
import random
from config import config  # Ensure config file includes necessary settings like dock capacities
from dock import Dock
from assembly_area import AssemblyArea
from resource_handler import ResourceHandler
from main import (
    generate_truck_arrivals,
    generate_orders,
    generate_loading_trucks,
    track_forklift_usage,
    calculate_average_utilization,
    truck_unloading_times,
    truck_loading_times,
    order_assembling_waiting_times,
    order_assembling_times,
    order_loading_mean_waiting_times,
    mean_pallet_put_times,
    mean_pallet_pickup_times
)

# FastAPI application instance
app = FastAPI()

# Global variables to store the simulation environment and results
env = None
dock_list = []
assembly_area_list = []
loading_dock_list = []
resource_handler = None

# Result storage for metrics
simulation_results = {}

app = FastAPI()

# Define a model for updating configuration
class ConfigUpdate(BaseModel):
    key: str  # Key to be updated
    value: str  # New value


@app.get("/config")
def get_config():
    """Retrieve the current configuration."""
    return config


@app.put("/config")
def update_config(update: ConfigUpdate):
    """Update a specific configuration key."""
    key, value = update.key, update.value
    if key not in config:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found.")

    # Attempt type casting the value to match the original type in the config
    original_value = config[key]
    try:
        if isinstance(original_value, int):
            value = int(value)
        elif isinstance(original_value, float):
            value = float(value)
        elif isinstance(original_value, list):
            value = eval(value)  # Caution: only use eval here for controlled inputs
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Value type mismatch for '{key}'. Expected {type(original_value).__name__}.",
        )

    config[key] = value
    return {"message": f"Config '{key}' updated successfully.", "new_value": value}


@app.post("/start-simulation/")
async def start_simulation():
    """
    Start the logistics simulation with settings from the config file.
    """
    global env, dock_list, assembly_area_list, loading_dock_list, resource_handler, simulation_results

    # Initialize random seed
    random.seed(config.get("random_seed", None))

    # Initialize simulation environment
    env = simpy.Environment()

    # Generate dock and assembly area coordinates based on config
    unloading_dock_start_y = 5
    width_unloading_dock = 5
    unloading_dock_end_y = unloading_dock_start_y + width_unloading_dock * config["num_unloading_docks"] + config["num_unloading_docks"] - 1
    unloading_dock_x = 2

    assembly_area_start_x = 32
    width_assembly_area = 6
    assembly_area_end_x = assembly_area_start_x + width_assembly_area * config["num_assembly_area"]
    assembly_area_y = -5

    loading_dock_start_x = 32
    width_loading_dock = 6
    loading_dock_end_x = loading_dock_start_x + width_loading_dock * config["num_loading_docks"]
    loading_dock_y = -11

    # Create resources: docks, assembly areas, and loading docks
    dock_list = [Dock(dock_id, (unloading_dock_x, round(y, 2), 0))
                 for dock_id, y in zip(range(1, config["num_unloading_docks"] + 1),
                                       np.arange(unloading_dock_start_y, unloading_dock_end_y, width_unloading_dock))]

    assembly_area_list = [AssemblyArea(area_id, (round(x, 2), assembly_area_y, 0), config["assembly_area_capacity"])
                          for area_id, x in zip(range(1, config["num_assembly_area"] + 1),
                                                np.arange(assembly_area_start_x, assembly_area_end_x, width_assembly_area))]

    loading_dock_list = [Dock(dock_id, (round(x, 2), loading_dock_y, 0))
                         for dock_id, x in zip(range(1, config["num_loading_docks"] + 1),
                                               np.arange(loading_dock_start_x, loading_dock_end_x, width_loading_dock))]

    # Initialize resource handler
    resource_handler = ResourceHandler(
        env,
        num_forklifts=config["forklifts"],
        num_unloading_docks=config["num_unloading_docks"],
        num_loading_docks=config["num_loading_docks"],
        num_assembly_areas=config["num_assembly_area"]
    )

    # Define simulation processes
    env.process(generate_truck_arrivals(env, resource_handler, resource_handler.unloading_docks, dock_list))
    env.process(generate_orders(env, resource_handler, assembly_area_list))
    env.process(generate_loading_trucks(env, resource_handler, assembly_area_list, loading_dock_list))
    env.process(track_forklift_usage(env, resource_handler))

    # Run the simulation
    env.run(until=config["simulation_duration_minutes"])

    # Calculate results
    total_time = config["simulation_duration_minutes"]
    simulation_results = {
        "Unloading Dock Utilization (%)": resource_handler.get_unloading_dock_utilization(total_time),
        "Storage Utilization (%)": resource_handler.get_storage_utilization(),
        "Loading Dock Utilization (%)": resource_handler.get_loading_dock_utilization(total_time),
        "Average Forklift Utilization (%)": calculate_average_utilization(
            total_time, resource_handler.forklifts.capacity
        ),
        "Truck Unloading Mean Time (mins)": np.mean(truck_unloading_times) if truck_unloading_times else None,
        "Truck Loading Mean Time (mins)": np.mean(truck_loading_times) if truck_loading_times else None,
        "Order Loading Wait Time (mins)": np.mean(order_loading_mean_waiting_times) if order_loading_mean_waiting_times else None,
        "Order Assembly Mean Wait Time (mins)": np.mean(order_assembling_waiting_times) if order_assembling_waiting_times else None,
        "Order Assembly Mean Time (mins)": np.mean(order_assembling_times) if order_assembling_times else None,
        "Pallet Put Mean Time (mins)": np.mean(mean_pallet_put_times) if mean_pallet_put_times else None,
        "Pallet Pickup Mean Time (mins)": np.mean(mean_pallet_pickup_times) if mean_pallet_pickup_times else None
    }

    return {"message": "Simulation completed", "results": simulation_results}



@app.get("/simulation-results/")
async def get_simulation_results():
    """
    Retrieve results of the most recent simulation.
    """
    if not simulation_results:
        return {"error": "No simulation results available. Please start a simulation first."}
    return {"results": simulation_results}
