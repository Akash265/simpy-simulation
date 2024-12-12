import random
from collections import deque
from config import config
from pallet import Pallet

class Storage:
    def __init__(self, num_aisles, num_levels, positions_per_level):
        # Initialization remains the same...
        self.num_aisles = num_aisles
        self.num_levels = num_levels
        self.positions_per_level = positions_per_level

        # Create the storage structure
        self.storage = {
            (aisle, level): deque()
            for aisle in range(num_aisles)
            for level in range(num_levels)
        }
        self.total_capacity = num_aisles * num_levels * positions_per_level
        self.current_items = 0

    def assign_storage_location(self, item, strategy="random"):
        """Assign a storage location for the item."""
        if self.current_items >= self.total_capacity:
            raise ValueError("Storage is full. Cannot assign location.")

        if strategy == "random":
            # Attempt random assignment until space is found
            attempts = 0
            while attempts < 10:  # Limit attempts to prevent infinite loop
                aisle = random.randint(0, self.num_aisles - 1)
                level = random.randint(0, self.num_levels - 1)
                location = (aisle, level)
                if len(self.storage[location]) < self.positions_per_level:
                    self.storage[location].append(item)
                    self.current_items += 1
                    return location
                attempts += 1
            raise ValueError("Unable to find space using random strategy.")

        elif strategy == "dedicated":
            aisle = hash(item.item_type) % self.num_aisles
            level = 0
            location = (aisle, level)
            if len(self.storage[location]) < self.positions_per_level:
                self.storage[location].append(item)
                self.current_items += 1
                return location
            else:
                raise ValueError(f"No space at dedicated location {location}.")
        else:
            raise ValueError("Unsupported storage strategy.")


    def pick_item(self, item_id, strategy="FIFO"):
        """Retrieve an item from storage based on the strategy."""
        for location, items in self.storage.items():
            if strategy == "FIFO" and items and items[0].item_id == item_id:
                self.current_items -= 1
                return location, items.popleft()
            elif strategy == "LIFO" and items and items[-1].item_id == item_id:
                self.current_items -= 1
                return location, items.pop()
        raise ValueError(f"Item {item_id} not found in storage.")

    def get_storage_state(self):
        """Return the current storage state."""
        return {
            location: [item.item_id for item in items]
            for location, items in self.storage.items()
        }
        
    def get_available_quantity(self, pallet_type):
        """Get the total available quantity of a specific pallet type."""
        total = 0
        for location, items in self.storage.items():
            total += sum(1 for item in items if item.pallet_type == pallet_type)
        return total
    def get_storage_utilization(self):
        """Calculate the percentage of storage capacity filled."""
        return (self.current_items / self.total_capacity) * 100
    
class AdvancedStorage:
    def __init__(self, num_aisles, slots_per_aisle, levels_per_slot, pallet_types):
        self.num_aisles = num_aisles
        self.slots_per_aisle = slots_per_aisle
        self.levels_per_slot = levels_per_slot
        self.pallet_types = pallet_types
        self.forklifts_per_unloading_dock = config["forklifts_per_unload_dock"]
        self.total_capacity = self.num_aisles*self.slots_per_aisle*self.levels_per_slot
        
        # Group aisles into 1-2-2-2-2-2-2-2-1 arrangement for two sections.
        self.grouped_aisles = self._group_aisles()
        self.aisle_assignment = self._assign_aisles_to_pallets()
        
        # Coordinates for each slot and level in each aisle (sections and aisles)
        self.coordinates = self._generate_coordinates()
        
        # Storage setup for pallets
        self.storage = self._initialize_storage()
        self.pallet_space = self._initialize_pallet_space()

    def _group_aisles(self):
        
        grouped_aisles = {}
        
        # Define the aisle groups (1-2-2-2-2-2-2-2-1 arrangement)
        section_1_aisles = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        section_2_aisles = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
        
        # Split aisles according to the pattern 1-2-2-2-2-2-2-2-1
        pattern = [1, 2, 2, 2, 2, 2, 2, 2, 1]
        
        # First section
        section_1_aisles_grouped = []
        for count in pattern:
            section_1_aisles_grouped.append((section_1_aisles[:count]))
            section_1_aisles = section_1_aisles[count:]
        
        # Second section
        section_2_aisles_grouped = []
        for count in pattern:
            section_2_aisles_grouped.append((section_2_aisles[:count]))
            section_2_aisles = section_2_aisles[count:]
        grouped_aisles["Section 1"] = section_1_aisles_grouped
        grouped_aisles["Section 2"] =section_2_aisles_grouped
            
        return grouped_aisles
    
    def _assign_aisles_to_pallets(self):
        """
        Assign aisles to pallet types based on the 1-2-2-2-2-2-2-2-1 aisle grouping for two sections.
        First section gets the first 4 pallet types, next section gets the last 4 pallet types.
        """
        aisle_assignment = {}

        section_1_aisles = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        section_2_aisles = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
        
        # Assign aisles to pallet types
        # First 4 pallet types to first section
        for i, pallet_type in enumerate(self.pallet_types[:4]):
            aisle_assignment[pallet_type] = section_1_aisles[i*4:(i+1)*4]
        
        # Next 4 pallet types to second section
        for i, pallet_type in enumerate(self.pallet_types[4:]):
            aisle_assignment[pallet_type] = section_2_aisles[i*4:(i+1)*4]
        
        return aisle_assignment

    def _generate_coordinates(self):
        """
        Generate coordinates (x, y, z) for each slot and level in each aisle and section.
        """
        coordinates = {}

        # Start positions for each section (Section 1 and Section 2)
        section_1_start_x = 14  # Section 1 starts at x=6
        y_start = 1
        gap_between_sections = 4
        each_slot_width = 1
        each_aisle_width = 1
        each_section_width  =  self.slots_per_aisle*each_slot_width
        gap_between_aisles = 3
        section_2_start_x = section_1_start_x + gap_between_sections + each_section_width  # 3-unit gap + Section 1 width
        
        # Define aisles per section (16 aisles per section)
        section_1_aisles = range(0, 16)
        section_2_aisles = range(16, 32)
        
        # For each section, we will assign coordinates to the aisles, slots, and levels
        for section_idx, section_start_x in enumerate([section_1_start_x, section_2_start_x]):
            section_name = f"Section {section_idx + 1}"
            section_coordinates = []
            aisles = section_1_aisles if section_idx == 0 else section_2_aisles
            aisles = self.grouped_aisles[section_name]
            y = y_start
            for grp in aisles:
                for aisle in grp:
                    aisle_coordinates = []
                    x = section_start_x
                    for slot in range(self.slots_per_aisle):
                        for level in range(self.levels_per_slot):
                            # Calculate the coordinate for each slot and level in the aisle
                            # The y-coordinate is the aisle number
                            # The x-coordinate is the section's start position + (20 units per aisle * aisle number)
                            # The z-coordinate is the level number
                            z = level  # Each level has a height of 1 unit
                            # Store the coordinate
                            aisle_coordinates.append((x, y, z))
                            coordinates[(aisle,slot,level)]=(x,y,z)
                        x += each_slot_width
                    section_coordinates.append(aisle_coordinates)
                    if aisle + 1 in grp:y +=each_aisle_width*2
                    else: y+=gap_between_aisles
        
        return coordinates
    
    def _initialize_storage(self):
        """
        Initialize the storage system with all locations set to None (empty).
        """
        storage = {}
        for aisle in range(self.num_aisles):
            storage[aisle] = []
            for slot in range(self.slots_per_aisle):
                storage[aisle].append([None] * self.levels_per_slot)  # Levels initialized to None (empty)
        return storage
    

    def _initialize_pallet_space(self):
        """
        Initialize the available pallet space for each pallet type.
        """
        pallet_space = {pallet_type: [] for pallet_type in self.pallet_types}
        
        # For each pallet type, assign the available spaces in the aisles.
        for pallet_type in self.pallet_types:
            assigned_aisles = self.aisle_assignment.get(pallet_type, [])
            for aisle in assigned_aisles:
                for slot in range(self.slots_per_aisle):
                    for level in range(self.levels_per_slot):
                        pallet_space[pallet_type].append((aisle, slot, level))
        return pallet_space

    def initial_storage(self, initial):
        num_pallet_per_aisle= initial*self.total_capacity/self.num_aisles
        # Get the aisles assigned for the pallet type
        for pallet_type in self.pallet_types:
            # Search for the first available space in the assigned aisles
            assigned_aisles = self.aisle_assignment[pallet_type]
            for aisle in assigned_aisles:
                count = 0
                for slot in range(self.slots_per_aisle):
                    for level in range(self.levels_per_slot):
                        if count<=num_pallet_per_aisle:  # Check if the location is free
                            pallet = Pallet(f"Existing-Pallet", pallet_type)
                            pallet.location = self.coordinates[(aisle, slot, level)]
                            self.storage[aisle][slot][level] = pallet  # Store pallet
                            count+=1
                            #self.pallet_space[pallet_type].remove((aisle, slot, level))  # Remove from available space
                        else:
                            break

    def assign_storage_location(self, pallet):
        """
        Assign a storage location for the pallet based on its type.

        Parameters:
        - pallet_type: The type of the pallet (e.g., T1, T2).
        - pallet_id: Unique identifier for the pallet.

        Returns:
        - Location (aisle, slot, level) where the pallet was stored.
        """
        pallet_type = pallet.pallet_type
        if pallet_type not in self.aisle_assignment:
            raise ValueError(f"Unknown pallet type: {pallet_type}. Cannot assign storage.")

        # Get the aisles assigned for the pallet type
        assigned_aisles = self.aisle_assignment[pallet_type]

        # Search for the first available space in the assigned aisles
        for aisle in assigned_aisles:
            for slot in range(self.slots_per_aisle):
                for level in range(self.levels_per_slot):
                    if self.storage[aisle][slot][level] is None:  # Check if the location is free
                        self.storage[aisle][slot][level] = pallet  # Store pallet
                        #self.pallet_space[pallet_type].remove((aisle, slot, level))  # Remove from available space
                        return (aisle, slot, level), self.coordinates[(aisle, slot, level)]

        # If no space is available in the assigned aisles
        raise ValueError(f"No available space for pallet type {pallet_type}.")

    def retrieve_pallet(self, pallet_id):
        """
        Retrieve a pallet from the storage system based on its ID.

        Parameters:
        - pallet_id: The unique identifier for the pallet.

        Returns:
        - Location (aisle, slot, level) where the pallet was stored.
        """
        for aisle in range(self.num_aisles):
            for slot in range(self.slots_per_aisle):
                for level in range(self.levels_per_slot):
                    if self.storage[aisle][slot][level] == pallet_id:
                        # Remove the pallet and update available space
                        pallet_type = None
                        for p_type, spaces in self.pallet_space.items():
                            if (aisle, slot, level) in spaces:
                                pallet_type = p_type
                                break
                        self.storage[aisle][slot][level] = None
                        self.pallet_space[pallet_type].append((aisle, slot, level))  # Add back to available spaces
                        print(f"Pallet {pallet_id} retrieved from Aisle {aisle}, Slot {slot}, Level {level}.")
                        return (aisle, slot, level)

        raise ValueError(f"Pallet {pallet_id} not found.")
    def get_available_quantity(self, pallet_type):
        """
        Get the total available quantity of a specific pallet type.
        
        Parameters:
        - pallet_type: The type of the pallet (e.g., T1, T2).

        Returns:
        - The total quantity of pallets of the specified type currently in storage.
        """
        if pallet_type not in self.pallet_space:
            raise ValueError(f"Unknown pallet type: {pallet_type}. Cannot get available quantity.")
        
        total_quantity = 0

        # Iterate over aisles assigned to the pallet type
        assigned_aisles = self.aisle_assignment[pallet_type]
        for aisle in assigned_aisles:
            for slot in range(self.slots_per_aisle):
                for level in range(self.levels_per_slot):
                    # Check if the location is occupied and matches the pallet type
                    pallet = self.storage[aisle][slot][level]
                    if  pallet is not None:  # Location is occupied
                        if pallet.location == self.coordinates[(aisle, slot, level)]:
                            total_quantity += 1

        return total_quantity

    def get_item(self, pallet_type, strategy="FIFO"):
        """
        Retrieve a pallet from storage based on the specified strategy (FIFO or LIFO).

        Parameters:
        - pallet_id: The unique identifier of the pallet to retrieve.
        - strategy: The strategy for picking the item. Options are 'FIFO' or 'LIFO'.

        Returns:
        - A tuple containing the location (aisle, slot, level) and the pallet ID.

        Raises:
        - ValueError if the pallet is not found or the strategy is invalid.
        """
        if strategy not in ["FIFO", "LIFO"]:
            raise ValueError(f"Invalid strategy: {strategy}. Supported strategies are 'FIFO' and 'LIFO'.")

        # Get the aisles assigned for the pallet type
        assigned_aisles = self.aisle_assignment[pallet_type]

        for aisle in assigned_aisles:
            for slot in range(self.slots_per_aisle):
                if strategy == "FIFO":
                    # Search from the bottom level upwards
                    for level in range(self.levels_per_slot):
                        if self.storage[aisle][slot][level] != None:
                            # Remove the pallet
                            self.storage[aisle][slot][level] = None
                            # Update pallet space
                            self.pallet_space[pallet_type].append((aisle, slot, level))
                            return self.coordinates[aisle, slot, level]

                elif strategy == "LIFO":
                    # Search from the top level downwards
                    for level in range(self.levels_per_slot - 1, -1, -1):
                        if self.storage[aisle][slot][level] != None :
                            # Remove the pallet
                            self.storage[aisle][slot][level] = None
                            # Update pallet space
                            self.pallet_space[pallet_type].append((aisle, slot, level))
                            return self.coordinates[aisle, slot, level]
        # Raise an error if the pallet is not found
        raise ValueError(f"Pallet not found in storage.")
    def get_storage_utilization(self):
        """Calculate the percentage of storage capacity filled."""
        total_quantity = 0
        for aisle in range(self.num_aisles):
            for slot in range(self.slots_per_aisle):
                for level in range(self.levels_per_slot):
                    if self.storage[aisle][slot][level] != None:
                        total_quantity+=1
        return (total_quantity / self.total_capacity) * 100
    
    def _get_pallet_type(self, aisle, slot, level):
        
        """
        Helper function to identify the pallet type based on its location.

        Parameters:
        - aisle: The aisle number.
        - slot: The slot number.
        - level: The level number.

        Returns:
        - The pallet type as a string.
        """
        for pallet_type, spaces in self.pallet_space.items():
            if (aisle, slot, level) in spaces:
                return pallet_type
        return None


