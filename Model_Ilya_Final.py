import mesa
import math
import numpy as np
import operator
import random
import inspect

### SOIL: contains nutrients and antibiotics

class Soil(mesa.Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)


        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # amount of turns between refuels of nutrients
        self.refuel_timer = 60
        # amount of nutrients to refuel
        self.refuel_amount = 5000
        ################################
        ################################
        ################################

        self.age = 0
        self.pos = pos
        # temperature doesnt do anything
        self.temperature = 5
        # not that important due to the refuel sources
        self.nutrients = {
            "Type_a_food": 5000,
            "Type_b_food": 5000,
            "Type_c_food": 5000

        } 

        self.antibiotics = {

        }


    def step(self):
        self.age += 1
        if self.age % self.refuel_timer:
            self.nutrients = dict.fromkeys(self.nutrients, self.refuel_amount)
        return

### GET AVERGE POSITION

def get_average_pos(lst):
    if len(lst) == 0:
        return []
    x = 0
    y = 0
    counter = 0
    for pos in lst:
        x += pos[0]
        y += pos[1]
        counter += 1

    # returns a list with one tuple, which was needed for after the reset, should maybe be changed but works
    return [(round(x/counter), round(y/counter))]

### INTRODUCES VARIABILITY INTO BACTERIAL POPULATION: function to sample only psoitive values of a destribution centered around the mean value

def avoid_identical_clones(mean_value, variation_coefficient = 0.1, num_samples = 1):

    values = np.random.normal(mean_value, variation_coefficient * mean_value, num_samples)

    negative_indices = np.where(values <= 0)[0]

    while len(negative_indices) > 0:

        new_values = np.random.normal(mean_value, variation_coefficient*mean_value, len(negative_indices))
        values[negative_indices] = new_values
        negative_indices = np.where(values < 0)[0]

    return values

### DATA COLLECTOR: function to quantify each species at every time step

def get_num_bacteria_per_type(model, bacteria_type):
    bacteria = [a for a in model.schedule.agents if isinstance(a, bacteria_type)]
    return len(bacteria)

### CONSTANTS: 

s_mutens_radius = 0.75 # micrometers radius found in literature and taken as refrence
average_bacteria_area = 4 * math.pi * s_mutens_radius**2 # micrometers square, using sphere area formula to get bacterial area

### PREDATOR

class Type_a_1(mesa.Agent):

    def __init__(self, unique_id, model, pos, area, avrg_viability_time_type_a):
        super().__init__(unique_id, model)

####### Metabolism parameters: WARNING, changing these may be necessary but can also result in instant bacterial death

        self.area = avoid_identical_clones(area)
        self.split_area = avoid_identical_clones(average_bacteria_area * 1.3) #From reference paper + ChatGPT; area that is defines a point when a bacteria can divide
        self.min_area = average_bacteria_area * 0.3 # From reference paper; bacteria dies if its area is samller than this

        self.avaliability = 0.2 # From reference paper; local avaliability of nutrients in a spatial cell for each bacterium
        self.nutrient_uptake_ratio = avoid_identical_clones(0.3) # From the reference paper; portion of nutrients form the simulation cell that the bacteria can access at once
        self.energy_yield = 0.65 # Reference paper has 0.15, does not work in our case because then the produced_energy < survival_energy; fraction that represents much energy is obtained from the consumed nutrients
        self.maintenance = 0.1 # Reference paper. Units of energy that a unit of area requieres per each time step
        
        self.max_possible_consumption = 0 # The biggest amount of nutrients bacteria can access in its neighborhood; initially set to zero and then overwritten
        self.max_individual_uptake = 0 # The biggest amount of nutrients bacterium can phyiscally consume (depends on its area); initially set to zero and then overwritten
        self.energy_netto = 0 # Netto energy produced by bacteria during eating, if positive -> bacterium acquires area, if negative -> shrinks; initially set to zero and then overwritten

        self.average_viability_time = avrg_viability_time_type_a  # Viability time describes number of timesteps at which bacteria was under stress. Stress being either shriniking (aka negative netto energy), contact with antibiotica or no possibility for division when its area > split_area
        self.max_viability_time = np.round(avoid_identical_clones(self.average_viability_time)) # Maximum amount of times a bacteria can survive under stress
        self.viability_index = 0 # Initially set to zero and then gets added 1 for every time under stress and is then compared with the max_viability_time to determine if bacteria dies or not
        self.dying_chance = np.random.uniform(0.001, 0.01) # Each bacterium has a probability defined by the shown range to die at every time step

####### Simulation parameters: changing them redefines the entire simualtion and species behaviour but less then the previous parameters set; they are more technical

        self.max_num_bacteria_in_cell = 2 # Limit the number of bacteria in a single simulation cell
        self.reproduction_radius = 1 # Radius of the empty cells scanned for free space
        self.random_spread_chance = 0.33 # Probability at which bacterial will look for a free neighbor cell, eventhough its max_num_bacteria_in_cell is not reached
        self.scouting_radius = 1 # Max radius to look for stress bacteria types in the neighboring simulation cells
        self.stressed_by = [Type_a_2] # The bacteria types that stress this cell type
        self.stress_radius = 1 # Radius which defines how far the antibiotica will be spread when the bacteria is stressed
        self.nutrition_list = ["Type_a_food"] # Type of nutrients this bacteria type can consume

####### Initialization parameters: DONT CHANGE THEM

        self.pos = pos
        self.age = 0
        self.is_stressed = False
        self.is_eaten = False
   
    def step(self): # Function that is repsonsible for the time flow in the simulation; defines actions taken at each time step

        self.age += 1 # Bacteria ages every time step

        self.stress_reaction() # Stress reaction is executed (look below for waht this function does)

        if not self.is_eaten: # if bacteria is eaten it doesnt do anything. If it is not being eaten it executes the self explanatory functions
            self.eat()
            self.reproduce()
            self.die()


    def scout(self):  # Scans the area for stress factors, when found it gets stressed

        positions = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True, radius=self.scouting_radius
        ) # scanned positions

        inhabitants = self.model.grid.get_cell_list_contents(positions) # objects on position
        for inhabitant in inhabitants:
            for bacteria in self.stressed_by:
                if isinstance(inhabitant, bacteria): # If an inhabitant is on stressed_by list, bacteria gets stressed
                    return True
        return False
    
    def stress_reaction(self):

        self.is_stressed = self.scout() # Scout function is executed (see above)

        if self.is_stressed: # If bacteria is stressed it spreads antibiotica 

            neighboring_cells = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=True, radius=self.stress_radius
            )

            for cell in neighboring_cells:
                soil = self.model.grid.get_cell_list_contents([cell])[0]

                if 'Type_a_2_X' in soil.antibiotics:
                    soil.antibiotics['Type_a_2_X'] += 1
                else:
                    soil.antibiotics['Type_a_2_X'] = 1
   
    def eat(self): # Nutrient consumntion process

        self_contents = self.model.grid.get_cell_list_contents([self.pos])
        soil = list(filter(lambda x: isinstance(x, Soil), self_contents))[0] # Get the soil object
        
        for nutrient in self.nutrition_list:
            if nutrient in soil.nutrients and soil.nutrients[nutrient] > 0: # If there are avaliable nutrients compute how many nutrients will be consumed

                self.max_possible_consumption = self.avaliability * soil.nutrients[nutrient] # The biggest amount each bacterium can consume depending on the nutrients amount
                self.max_individual_uptake = self.area * self.nutrient_uptake_ratio # The biggest amount each bacterium can consume depending on the bacteria area
                if self.max_possible_consumption >= self.max_individual_uptake: # Pick the smaller of the upper bounds
                    actual_consumption = self.max_individual_uptake 
                else: 
                    actual_consumption = self.max_possible_consumption

                soil.nutrients[nutrient] -= actual_consumption
                self.energy_netto = self.energy_yield * actual_consumption  - self.maintenance * self.area # energy coming from the consumed nutrients (produced) - the energy that bacteria needs to survive (maintenance)

                if self.energy_netto >= 0: # If the netto energy is non-negative bacteria converts the produced energy into area
                    self.area += self.energy_netto * 0.5 # The increment factor (0.5) is from reference paper
                else: # If it is negative bacteria's area shrinks
                    self.area = 0.9 * self.area # The shrincage factor (0.9) id from reference paper
                    self.viability_index += 1
            
    def reproduce(self): 

        if self.area >= self.split_area: # Only reproduce if the area is big enough forn that, if not increase the viability index

            self_contents = self.model.grid.get_cell_list_contents([self.pos])
            self_contents_bacteria = list(filter(lambda x: not isinstance(x, Soil), self_contents))

            if len(self_contents_bacteria) >= self.max_num_bacteria_in_cell or self.random.random() < self.random_spread_chance:  # Spread to the neighboring simulation cells if one of the conditions met
                if len(self.model.free_space[f'{Type_a_1}_coordinates']) > 0: # If there is a free positions for this bacteria type it will push the mother cell there and reproduce the daughter cell into mother's original location

                    reproduction_pos = self.pos
                    self.model.grid.move_agent(self, self.model.free_space[f'{Type_a_1}_coordinates'][0])
                    del self.model.free_space[f'{Type_a_1}_coordinates'][0]

                    new_bacteria= Type_a_1(self.model.next_id(), self.model, reproduction_pos, self.area * 0.5, self.average_viability_time)
                    self.area = self.area * 0.5
                    self.max_individual_uptake = self.area * self.nutrient_uptake_ratio
        
                    self.model.grid.place_agent(new_bacteria, reproduction_pos)
                    self.model.schedule.add(new_bacteria)
                
                else: # If there is no space avaliable then the viability index gets increased
                    self.viability_index += 1

            else: # Otherwise reproduce in its own simulation cell   

                reproduction_pos = self.pos
                new_bacteria= Type_a_1(self.model.next_id(), self.model, reproduction_pos, self.area * 0.5, self.average_viability_time)
                self.area = self.area * 0.5
                self.max_individual_uptake = self.area * self.nutrient_uptake_ratio
        
                self.model.grid.place_agent(new_bacteria, reproduction_pos)
                self.model.schedule.add(new_bacteria)

        else:
            self.viability_index += 1
    
    def die(self):
        
        if  (self.area < self.min_area) or (self.viability_index >= self.max_viability_time) or (self.random.random() < self.dying_chance): # Death if one of the conditions is met
                
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)

### PREY

class Type_a_2(mesa.Agent):

    def __init__(self, unique_id, model, pos, area, avrg_viability_time_type_a, immediate_killing, aggressiveness):
        super().__init__(unique_id, model)

####### Metabolism parameters: WARNING, changing these may be necessary but can also result in instant bacterial death

        self.area = avoid_identical_clones(area)
        self.split_area = avoid_identical_clones(average_bacteria_area * 1.3) #From reference paper + ChatGPT; area that is defines a point when a bacteria can divide
        self.min_area = average_bacteria_area * 0.3 # From reference paper; bacteria dies if its area is samller than this

        self.avaliability = 0.2 # From reference paper; local avaliability of nutrients in a spatial cell for each bacterium
        self.nutrient_uptake_ratio = avoid_identical_clones(0.3) # From the reference paper; portion of nutrients form the simulation cell that the bacteria can access at once
        self.energy_yield = 0.65 # Reference paper has 0.15, does not work in our case because then the produced_energy < survival_energy; fraction that represents much energy is obtained from the consumed nutrients
        self.maintenance = 0.1 # Reference paper. Units of energy that a unit of area requieres per each time step
        
        self.max_possible_consumption = 0 # The biggest amount of nutrients bacteria can access in its neighborhood; initially set to zero and then overwritten
        self.max_individual_uptake = 0 # The biggest amount of nutrients bacterium can phyiscally consume (depends on its area); initially set to zero and then overwritten
        self.energy_netto = 0 # Netto energy produced by bacteria during eating, if positive -> bacterium acquires area, if negative -> shrinks; initially set to zero and then overwritten

        self.average_viability_time = avrg_viability_time_type_a  # Viability time describes number of timesteps at which bacteria was under stress. Stress being either shriniking (aka negative netto energy), contact with antibiotica or no possibility for division when its area > split_area
        self.max_viability_time = np.round(avoid_identical_clones(self.average_viability_time)) # Maximum amount of times a bacteria can survive under stress
        self.viability_index = 0 # Initially set to zero and then gets added 1 for every time under stress and is then compared with the max_viability_time to determine if bacteria dies or not
        self.dying_chance = np.random.uniform(0.001, 0.01) # Each bacterium has a probability defined by the shown range to die at every time step

        self.immediate_killing = immediate_killing # If True bacteria dies when it comes in contact with antibiotica with a probability that is equal to aggressiveness; if False netto energy is decreased by a factot that is equal to agressiveness
        self.average_aggressiveness = aggressiveness
        self.aggressiveness  = avoid_identical_clones(self.average_aggressiveness)

####### Simulation parameters: changing them redefines the entire simualtion and species behaviour but less then the previous parameters set; they are more technical

        self.max_num_bacteria_in_cell = 2 # Limit the number of bacteria in a single simulation cell
        self.reproduction_radius = 1 # Radius of the empty cells scanned for free space
        self.random_spread_chance = 0.33 # Probability at which bacterial will look for a free neighbor cell, eventhough its max_num_bacteria_in_cell is not reached
        self.nutrition_list = ["Type_a_food"] # Type of nutrients this bacteria type can consume
        self.antibiotics_list = ["Type_a_2_X"] # Antibiotica type that affects the bacteria

####### Initialization parameters: DONT CHANGE THEM

        self.pos = pos
        self.age = 0
        self.is_eaten = False

    def step(self): # Function that is repsonsible for the time flow in the simulation; defines actions taken at each time step

        self.age += 1 # Bacteria ages every time step

        if not self.is_eaten: # if bacteria is eaten it doesnt do anything. If it is not being eaten it executes the self explanatory functions
            self.eat()
            self.reproduce()
            self.die()
 
    def eat(self): # Nutrient consumntion process

        self_contents = self.model.grid.get_cell_list_contents([self.pos])
        soil = list(filter(lambda x: isinstance(x, Soil), self_contents))[0] # Get the soil object

        for nutrient in self.nutrition_list:
            if nutrient in soil.nutrients and soil.nutrients[nutrient] > 0:
            
                self.max_possible_consumption = self.avaliability * soil.nutrients[nutrient] # The biggest amount each bacterium can consume depending on the nutrients amount
                self.max_individual_uptake = self.area * self.nutrient_uptake_ratio # The biggest amount each bacterium can consume depending on the bacteria area
                if self.max_possible_consumption >= self.max_individual_uptake: # Pick the smaller of the upper bounds
                    actual_consumption = self.max_individual_uptake 
                else: 
                    actual_consumption = self.max_possible_consumption

                soil.nutrients[nutrient] -= actual_consumption
                self.energy_netto = self.energy_yield * actual_consumption  - self.maintenance * self.area # energy coming from the consumed nutrients (produced) - the energy that bacteria needs to survive (maintenance)
        
                for antibiotic in self.antibiotics_list:
                    if antibiotic in soil.antibiotics and soil.antibiotics[antibiotic] > 0 and self.immediate_killing == False: # If there is an antibiotic in the soil and the immediate killing is false the netto energy is decreased by the aggressiveness term
                        self.energy_netto -= abs(self.energy_netto) * self.aggressiveness 
                        self.viability_index += 1
                        soil.antibiotics[antibiotic] -= 1

                if self.energy_netto >= 0: # If the netto energy is non-negative bacteria converts the produced energy into area
                    self.area += self.energy_netto * 0.5 # The increment factor (0.5) is from reference paper
                else: # If it is negative bacteria's area shrinks
                    self.area = 0.9 * self.area # The shrincage factor (0.9) id from reference paper
                    self.viability_index += 1
            
    def reproduce(self):

        if self.area >= self.split_area: # Only reproduce if the area is big enough forn that, if not increase the viability index

            self_contents = self.model.grid.get_cell_list_contents([self.pos])
            self_contents_bacteria = list(filter(lambda x: not isinstance(x, Soil), self_contents))

            if len(self_contents_bacteria) >= self.max_num_bacteria_in_cell or self.random.random() < self.random_spread_chance:  # Spread to the neighboring simulation cells if one of the conditions met 
                if len(self.model.free_space[f'{Type_a_2}_coordinates']) > 0: # If there is a free positions for this bacteria type it will push the mother cell there and reproduce the daughter cell into mother's original location

                    reproduction_pos = self.pos
                    self.model.grid.move_agent(self, self.model.free_space[f'{Type_a_2}_coordinates'][0])
                    del self.model.free_space[f'{Type_a_2}_coordinates'][0]

                    new_bacteria= Type_a_2(self.model.next_id(), self.model, reproduction_pos, self.area * 0.5, self.average_viability_time, self.immediate_killing, self.average_aggressiveness)
                    self.area = self.area * 0.5
                    self.max_individual_uptake = self.area * self.nutrient_uptake_ratio
        
                    self.model.grid.place_agent(new_bacteria, reproduction_pos)
                    self.model.schedule.add(new_bacteria)
                
                else: # If there is no space avaliable then the viability index gets increased
                    self.viability_index += 1

            else: # Otherwise reproduce in its own simulation cell  

                reproduction_pos = self.pos
                new_bacteria= Type_a_2(self.model.next_id(), self.model, reproduction_pos, self.area * 0.5, self.average_viability_time, self.immediate_killing, self.average_aggressiveness)
                self.area = self.area * 0.5
                self.max_individual_uptake = self.area * self.nutrient_uptake_ratio
        
                self.model.grid.place_agent(new_bacteria, reproduction_pos)
                self.model.schedule.add(new_bacteria)

        else:
            self.viability_index += 1

    def die(self):

        if (self.area < self.min_area) or (self.viability_index >= self.max_viability_time) or (self.random.random() < self.dying_chance): # Death if one of the conditions is met
                          
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)

        elif (self.immediate_killing == True) and (self.random.random() < self.aggressiveness): # Speacial death case if immediate killing is true and antibiotics have to be considered
                
            self_contents = self.model.grid.get_cell_list_contents([self.pos])
            soil = list(filter(lambda x: isinstance(x, Soil), self_contents))[0]
            for antibiotic in self.antibiotics_list:
                if antibiotic in soil.antibiotics and soil.antibiotics[antibiotic] > 0:
                    soil.antibiotics[antibiotic] -= 1
                    self.model.grid.remove_agent(self)
                    self.model.schedule.remove(self)

### MODEL

class Microbiome(mesa.Model):
    """A model with some number of agents."""
    # EVERYTHING WITH FIVE HASHTAGS IS RELATED TO INITIAL MESA SCAFFOLD AND COULD BE USEFULL IN THE FUTURE

    def __init__(self, num_type_a_1, num_type_a_2, is_torus, grid_height, grid_width, immediate_killing, aggressiveness, avrg_viability_time_type_a,# Compulsory inputs for the simulation
                 avrg_area_type_a = average_bacteria_area): # Variables that have a default value but can be changed

        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # grid_width and grid_height also need to be changed in server.py for visualisation:
        # canvas_element = mesa.visualization.CanvasGrid(bacteria_portrayal, self.grid_width, self.grid_height, 500, 500)
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.decimal_aggressiveness = aggressiveness / 100

        # All used for quantifying the initial conditions
        self.a1_edge_distance = []
        self.a2_edge_distance = []
        self.a2_competition_index = []
        
        # decides after how many turns the random direction of the type_d swarms changes
        # prevents the swarm from going back and forth 
        # done in the model for the whole swarm, so it doesnt spread
        #self.swarm_direction_turns = 10
        # decides if the swarm moves in percentage 0 = 0%, 1 = 100% --> 1 means swarm moves every time
        # done in the model for the whole swarm, so it doesnt spread
        # self.swarm_chance_move = 1
        # stops reproduction after population reaches a limit

        ##### REMOVED THE UPPER BOUND FOR POPULATIONS

        ##### self.type_a_population_limit = type_a_population_limit

        ##### self.type_d_population_limit = type_d_population_limit
        # reproduction spread pattern, if True includes all 8 surrounding squares, False means only up/down/left/right
        self.reproduction_spread_moore = True
        # limits the number of bacteria in a single cell for performance and better spreading
        self.max_num_bacteria_in_cell = 2
        ################################
        ################################
        ################################

        self.running = True
        self.current_id = 1
        self.step_num = 1
        self.directions = ["left", "right", "up", "down"]

        self.grid = mesa.space.MultiGrid(self.grid_width, self.grid_height, is_torus)
        
        # different schedulers can be found here
        # https://mesa.readthedocs.io/en/latest/apis/time.html
        self.schedule = mesa.time.RandomActivation(self)

        # Create Soil
        for i in range(self.grid.width):
            for j in range(self.grid.height):
                soil = Soil(self.next_id(), self, (i, j))
                self.schedule.add(soil)
                self.grid.place_agent(soil, (i, j))

        # Create Type_a_1
        self.a1_initial_pos = [] 
        for i in range(num_type_a_1):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            a = Type_a_1(self.next_id(), self, (x, y), avrg_area_type_a, avrg_viability_time_type_a)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (x, y))
            self.a1_initial_pos.append((x,y))
            

        # Create Type_a_2
        self.a2_initial_pos = []
        self.a1_initial_aggressiveness = []
        for i in range(num_type_a_2):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            a = Type_a_2(self.next_id(), self, (x, y), avrg_area_type_a, avrg_viability_time_type_a, immediate_killing, self.decimal_aggressiveness)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (x, y))
            self.a2_initial_pos.append((x,y))
            self.a1_initial_aggressiveness.append(a.aggressiveness)

        self.initial_conditions = self.quantify_initial_conditions()    

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "A1_Initial_Edge_Distance": lambda m: np.mean(m.a1_edge_distance),
                "A2_Initial_Edge_Distance": lambda m: np.mean(m.a2_edge_distance),
                "A1_Initial_Aggressiveness": lambda m: np.round(np.median(m.a1_initial_aggressiveness) * 100, 2),
                "A2_Initial_Competition_Index": lambda m: np.round(np.median(m.a2_competition_index), 2),
                "A1_Number": [get_num_bacteria_per_type, [self, Type_a_1]],
                "A2_Number": [get_num_bacteria_per_type, [self, Type_a_2]]
            }
        )  

# Computes the minimum distsnce till edge for each bacteria and the ratio of the own type next to it
    def quantify_initial_conditions(self):

        width = self.grid.width
        height = self.grid.height

        all_edges = [(x, 0) for x in range(width)] + \
            [(x, height - 1) for x in range(width)] + \
            [(0, y) for y in range(height)] + \
            [(width - 1, y) for y in range(height)]

        for a1 in self.a1_initial_pos:

            a1_distances = [np.linalg.norm(np.array([a1[0] - edge_x, a1[1] - edge_y])) for edge_x, edge_y in all_edges]
            a1_min_distance = min(a1_distances)
            self.a1_edge_distance.append(a1_min_distance)

        for a2 in self.a2_initial_pos:

            a2_distances = [np.linalg.norm(np.array([a2[0] - edge_x, a2[1] - edge_y])) for edge_x, edge_y in all_edges]
            a2_min_distance = min(a2_distances)
            self.a2_edge_distance.append(a2_min_distance)

            intial_contents = self.grid.get_neighbors(a2, moore = True, include_center = False, radius = 5)
            initial_bacteria = list(filter(lambda x: not isinstance(x, Soil), intial_contents))

            if len(initial_bacteria) == 0:
                self.a2_competition_index.append(0)
            else:
                initial_a1 = list(filter(lambda x: isinstance(x, Type_a_1), initial_bacteria))
                self.a2_competition_index.append(len(initial_a1)/len(initial_bacteria))
        
    def find_free_space(self, max_search_radius):

        classes = inspect.getmembers(
            inspect.getmodule(self.__class__), inspect.isclass)

        # Filter classes that inherit from Agent but exclude "Soil"
        agent_classes = [cls for name, cls in classes if issubclass(cls, mesa.Agent) and cls.__name__ != 'Soil']

        # Create a positional list for each bacteria agent
        positional_dict = {}
        for agent in agent_classes:

            list_name = f'{agent}_coordinates'
            positional_dict[list_name] = []

        all_coordinates = self.grid.get_neighborhood((0,0), moore = True, include_center = True, radius = max_search_radius)

        for a in all_coordinates:

            contents = self.grid.get_cell_list_contents(a)
            bacteria_contents = list(filter(lambda x: not isinstance(x, Soil), contents))
            free_space_avaliable = len(bacteria_contents) < self.max_num_bacteria_in_cell

            if free_space_avaliable:
                
                neighbors = self.grid.get_neighbors(a, moore =  True, include_center = False, radius = 1)
                bacteria_neighbors = list(filter(lambda x: not isinstance(x, Soil), neighbors))

                if len(bacteria_neighbors) > 0:

                    max_bacteria_neighbors = 0
                    main_neighbor =  None

                    for agent in agent_classes:
 
                        type_specific_neighbors = list(filter(lambda x: isinstance(x, agent), bacteria_neighbors))

                        if len(type_specific_neighbors) > max_bacteria_neighbors:
                    
                            max_bacteria_neighbors = len(type_specific_neighbors)
                            main_neighbor = agent
                    
                    positional_dict[f'{main_neighbor}_coordinates'].append(a)

        for key, position_list in positional_dict.items():
            self.random.shuffle(position_list)
           
        return positional_dict

    def step(self):
        
        self.step_num += 1

        # run agents
        
        self.free_space = self.find_free_space(max(self.grid_width, self.grid_height))
        self.datacollector.collect(self)
        self.schedule.step()