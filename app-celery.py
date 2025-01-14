from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
from database import SessionLocal, Base, engine, ConfigurationModel  # Assume SQLAlchemy setup
from celery import Celery
import simpy
import random
import numpy as np
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
import logging


app = FastAPI()

# Celery application instance
celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",  # Celery broker
    backend="redis://redis:6379/0"  # Celery results backend
)

# Database initialization
Base.metadata.create_all(bind=engine)

# Default config
default_config = {
    "forklifts": 40,
    "forklifts_per_unload_dock": 21,
    "forklifts_per_order_assembly": 20,
    "unloading_trucks_per_hour": 6,
    "loading_trucks_per_hour": 4,
    "orders_per_hour": 8,
    "truck_capacity_min": 20,
    "truck_capacity_max": 20,
    "minimum_order_size": 5,
    "maximum_order_size": 12,
    "assembly_area_capacity": 1000,
    "initial_storage": 0.2,
    "num_unloading_docks": 5,
    "num_assembly_area": 7,
    "num_loading_docks": 7,
    "simulation_duration_minutes": 1440,
    "storage_aisles": 32,
    "storage_slots_per_aisle": 38,
    "storage_levels_per_slot": 5,
    "forklift_speed_xy": 3,
    "lever_speed_z": 5,
}
def convert_config_types(config: dict) -> dict:
    """Convert configuration values to their proper types."""
    type_mapping = {
        "forklifts": int,
        "forklifts_per_unload_dock": int,
        "forklifts_per_order_assembly": int,
        "unloading_trucks_per_hour": int,
        "loading_trucks_per_hour": int,
        "orders_per_hour": int,
        "truck_capacity_min": int,
        "truck_capacity_max": int,
        "minimum_order_size": int,
        "maximum_order_size": int,
        "assembly_area_capacity": int,
        "initial_storage": float,
        "num_unloading_docks": int,
        "num_assembly_area": int,
        "num_loading_docks": int,
        "simulation_duration_minutes": int,
        "storage_aisles": int,
        "storage_slots_per_aisle": int,
        "storage_levels_per_slot": int,
        "forklift_speed_xy": float,
        "lever_speed_z": float
    }
    
    converted_config = {}
    for key, value in config.items():
        if key in type_mapping and value is not None:
            try:
                converted_config[key] = type_mapping[key](value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for {key}: {value}. Expected type: {type_mapping[key].__name__}"
                )
        else:
            converted_config[key] = value
    return converted_config

@app.post("/configurations/")
def create_configuration(updated_config: Dict[str, Optional[object]]):
    """
    Update default configurations and store in the database.
    """
    db = SessionLocal()
    new_config = {**default_config, **updated_config}  # Merge default and user-provided config
    try:
        # Convert config values to proper types before storing
        converted_config = convert_config_types(new_config)
        config_model = ConfigurationModel(config=converted_config)
        db.add(config_model)
        db.commit()
        db.refresh(config_model)
        return {"message": "Configuration saved.", "config_id": config_model.id}
    except HTTPException as e:
        db.rollback()
        raise e
    finally:
        db.close()

@app.get("/configurations/")
def list_configurations():
    """
    Fetch all saved configurations.
    """
    db = SessionLocal()
    configs = db.query(ConfigurationModel).all()
    db.close()
    return {"configurations": [{"id": c.id, "config": c.config} for c in configs]}

# Result storage for metrics
simulation_results = {}

@app.post("/start-simulation/")
async def start_simulation(config_id: int, background_tasks: BackgroundTasks):
    """
    Start a simulation with the specified configuration.
    """
    try:
        logging.info(f"Received config_id: {config_id}")
        db = SessionLocal()
        config_entry = db.query(ConfigurationModel).filter(ConfigurationModel.id == config_id).first()
        
        if not config_entry:
            raise HTTPException(status_code=404, detail="Configuration not found.")
        
        # Convert config values to proper types before starting simulation
        converted_config = convert_config_types(config_entry.config)
        task = run_simulation.delay(converted_config)
        return {"message": "Simulation started.", "task_id": task.id}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error starting simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting simulation: {str(e)}")
    finally:
        db.close()


@app.get("/simulation-results/")
async def get_simulation_results(task_id: str):
    """
    Retrieve the results of the simulation using the Celery task ID.
    """
    task_result = celery_app.AsyncResult(task_id)

    if task_result.state == "PENDING":
        return {"status": "Simulation in progress. Please try again later."}
    elif task_result.state == "SUCCESS":
        return {"status": "Simulation completed.", "results": task_result.result}
    elif task_result.state == "FAILURE":
        return {"status": "Simulation failed.", "error": str(task_result.info)}

    return {"status": "Unknown task state."}

@celery_app.task
def run_simulation(config):
    """
    Perform the logistics simulation asynchronously.
    """
    try:

        """
        Perform the logistics simulation asynchronously.
        """
        global simulation_results
                # Convert config values to proper types before using
        config = convert_config_types(config)
        
        # Rest of your simulation code
        random.seed(config.get("random_seed", None))
        env = simpy.Environment()
            

        # Define resources as in the original start_simulation function
        dock_list = [
            Dock(dock_id, (2, y, 0))
            for dock_id, y in enumerate(
                np.arange(5, 5 + (config["num_unloading_docks"] * 5), 5), start=1
            )
        ]
        assembly_area_list = [
            AssemblyArea(area_id, (x, -5, 0), config["assembly_area_capacity"])
            for area_id, x in enumerate(
                np.arange(32, 32 + (config["num_assembly_area"] * 6), 6), start=1
            )
        ]
        loading_dock_list = [
            Dock(dock_id, (x, -11, 0))
            for dock_id, x in enumerate(
                np.arange(32, 32 + (config["num_loading_docks"] * 6), 6), start=1
            )
        ]

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

        # Collect metrics
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
        
        return simulation_results
    except Exception as e:
        logging.error(f"Simulation error: {str(e)}")
        raise
    





