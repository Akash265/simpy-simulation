import streamlit as st
import requests

# Define the base URL of the FastAPI server
BASE_URL = "http://localhost:8000"

# Helper function to fetch data from FastAPI
def fetch_data(endpoint):
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return None

# Update the post_data helper function to handle query parameters
def post_data(endpoint, json_data=None, params=None):
    try:
        response = requests.post(f"{BASE_URL}/{endpoint}", json=json_data, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            st.error(f"Invalid request format: {e.response.json()['detail']}")
        else:
            st.error(f"Error sending data to {endpoint}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending data to {endpoint}: {e}")
        return None

# Streamlit layout for Logistics Simulation Dashboard
st.title("Logistics Simulation Dashboard")

# Define tabs for configuration management, all configurations, and simulation results
tabs = st.radio("Select a Tab", options=["Configuration Management", "All Configurations", "Simulation Results"])

if tabs == "Configuration Management":
    st.header("Manage Configurations")
    
    # Display all configurations
    configurations = fetch_data("configurations/")
    if configurations and "configurations" in configurations:
        config_options = configurations["configurations"]
        selected_config = st.selectbox(
            "Select Configuration ID", options=[config["id"] for config in config_options]
        )
        
        # Display the selected configuration
        selected_config_data = next(
            (config for config in config_options if config["id"] == selected_config), {}
        )
        if selected_config_data:
            st.json(selected_config_data["config"])
    else:
        st.info("No configurations available. Add one to proceed.")
    
    # Form to create a new configuration
    with st.form("add_config_form"):
        st.subheader("Create New Configuration")
        new_config = {}
        for key, value in fetch_data("configurations/").get("configurations", [{}])[0]["config"].items():
            if isinstance(value, (int, float)):
                new_config[key] = st.number_input(f"{key}", value=value)
            else:
                new_config[key] = st.text_input(f"{key}", value=str(value))
        
        create_button = st.form_submit_button("Create Configuration")
        if create_button:
            result = post_data("configurations/", new_config)
            if result:
                st.success(result["message"])

elif tabs == "All Configurations":
    st.header("All Configurations")
    
    configurations = fetch_data("configurations/")
    if configurations and "configurations" in configurations:
        config_options = configurations["configurations"]
        
        # Display configurations in a selection list
        selected_config = st.selectbox(
            "Select Configuration ID to run simulation",
            options=[config["id"] for config in config_options]
        )
        
        # When user clicks run simulation, call backend API
        
    # Update the simulation button code
    if st.button("Run Simulation"):
        if selected_config:
            # Pass config_id as a query parameter
            response = post_data("start-simulation/", params={"config_id": selected_config})
            if response:
                st.success(response["message"])
                task_id = response.get("task_id")
                st.write(f"Task ID: {task_id}")
            else:
                st.warning("Please select a valid configuration to start the simulation.")
    else:
        st.info("No configurations available to run a simulation.")

elif tabs == "Simulation Results":
    st.header("Simulation Results")
    
    task_id_input = st.text_input("Enter Task ID to Retrieve Results")
    if st.button("Get Results"):
        if not task_id_input.strip():
            st.warning("Please provide a valid Task ID.")
        else:
            results = fetch_data(f"simulation-results/?task_id={task_id_input}")
            if results:
                if results.get("status") == "Simulation completed.":
                    st.json(results["results"])
                elif results.get("status") == "Simulation in progress. Please try again later.":
                    st.info("Simulation still in progress. Please check back later.")
                elif results.get("status") == "Simulation failed.":
                    st.error(f"Error: {results.get('error')}")
