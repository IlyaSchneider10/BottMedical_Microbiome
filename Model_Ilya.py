import mesa
import numpy as np
import operator

### SOIL

class Soil(mesa.Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)


        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # amount of turns between refuels of nutrients
        self.refuel_timer = 60
        # amount of nutrients to refuel
        self.refuel_amount = 2
        ################################
        ################################
        ################################

        self.age = 0
        self.pos = pos
        # temperature doesnt do anything
        self.temperature = 5
        # not that important due to the refuel sources
        self.nutrients = {
            # Type_a food
            "iron": 5000,
            # Type_b food
            "chicken":5000,
            # Type_c food
            "organic":5000

        } 

        self.antibiotics = {

        }


    def step(self):
        self.age += 1
        if self.age % self.refuel_timer:
            self.nutrients = dict.fromkeys(self.nutrients, self.refuel_amount)
    #    if self.random.random() < 0.001:
    #    #if self.age % 50 == 0 and self.random.random() < 0.5:
    #        self.nutrients = dict.fromkeys(self.nutrients, 2)
    #        possible_postitions = self.model.grid.get_neighborhood(
    #            self.pos, moore=False, include_center=False, radius=1
    #        )
    #        for position in possible_postitions:
    #            soil = self.model.grid.get_cell_list_contents([position])[0]
    #            soil.nutrients = dict.fromkeys(soil.nutrients, 1)
    #    self.nutrients = dict.fromkeys(self.nutrients, 1)
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

##### INTRODUCES VARIABILITY INTO BACTERIAL POPULATION

def avoid_identical_clones(mean_value, variation_coefficient = 0.1, num_samples = 1):

    values = np.random.normal(mean_value, variation_coefficient*mean_value, num_samples)

    negative_indices = np.where(values <= 0)[0] # avoid negative values from the distribution by selecting them by new positive values
    # ALTERNATIVE IDEA: the while loop can take away lots of computation -> instead of continuously drawing from ditribution till no more negative values are there
    # invert the negative values

    while len(negative_indices) > 0:

        new_values = np.random.normal(mean_value, variation_coefficient*mean_value, len(negative_indices))
        values[negative_indices] = new_values
        negative_indices = np.where(values < 0)[0]

    return values

### PREDATOR

class Type_a_1(mesa.Agent):

    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)

        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # spreads the dying, to not create big bumps in the graph
        # example: average 40 turns --> 1/40 = 0.025
        self.dying_chance = 0.025 # doesnt do anything, cant die on its own at the moment
        # acts as health of the bacteria
        self.sturdiness = 1
        # limits the number of bacteria in a single cell for performance and better spreading
        self.max_num_bacteria_in_cell = 2
        # if no cell with less than self.max_num_bacteria_in_cell is found, reproduction will not take place
        self.reproduction_radius = 2
        # chance to spread when self.max_num_bacteria_in_cell is not reached, to fasten the spread
        self.random_spread_chance = 0.1
        # scouting is done in a moore radius, scouting for stressed_by
        self.scouting_radius = 1
        # when a object of this type is found in the scouting radius, I get stressed
        self.stressed_by = [Type_a_2]
        # radius in which the antibiotica will be spread
        self.stress_radius = 4
        # nutrition and antibiotics need to be in the respective dict in the Soil object
        self.nutrition_list = ["iron"]
        ################################
        ################################
        ################################

        self.pos = pos
        self.age = 0
        self.has_eaten = False
        self.is_stressed = False
        
        
        # doesnt do anything when being eaten
        self.is_eaten = False


    # Wird bei jedem Durchgang aufgerufen
    def step(self):

        self.age += 1

        # looking for problems, triggers stress
        self.scout()

        # stress reaction
        if self.is_stressed:
            self.stress_reaction()

        # if bacteria is eaten by another thing, it doesnt do anything (it will be killed by the other party)
        if not self.is_eaten:
            self.eat()
            self.reproduce()
            self.die()

            ##### CAN BE SET AN UPPER LIMIT FOR NUMBER OF BACTERIA WITH THIS LOOP:
            
            # when maximum number in model is reached, reproduction is paused

            ##### if not self.model.reproduction_stop_a_1:
            #####    self.reproduce()
            ##### self.die()


    # scans the area for stress factors, when found, I get stressed
    def scout(self):
        # scanned positions
        positions = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True, radius=self.scouting_radius
        )

        # objects on position
        inhabitants = self.model.grid.get_cell_list_contents(positions)
        for inhabitant in inhabitants:
            for bacteria in self.stressed_by:

                # if inhabitant is on stressed_by list, I get stressed
                if isinstance(inhabitant, bacteria):
                    self.is_stressed = True
                    break
                else:
                    self.is_stressed = False
   

    # eat nutrients from soil    
    def eat(self):
        # get soil
        soil = self.model.grid.get_cell_list_contents([self.pos])[0]
        
        # if there are nutrients, first nutrient on nutrition_list gets consumed
        for nutrient in self.nutrition_list:
            # look if consumable nutrients in soil
            if nutrient in soil.nutrients and soil.nutrients[nutrient] > 0:
                # subract nutrient and set has_eaten
                soil.nutrients[nutrient] -= 1
                self.has_eaten = True
                break
                


    def reproduce(self):
        # reproduces once eaten
        if self.has_eaten:

            # Wenn bereits mehr als max_num_bacteria_in_cell Bakteriean auf einem Feld sind, oder Zufällig random_spread_chance
            if len(self.model.grid.get_cell_list_contents([self.pos])) > self.max_num_bacteria_in_cell or self.random.random() < self.random_spread_chance:
                
                # if it spreads, we randomly look for a position in the neighborhood
                possible_postitions = self.model.grid.get_neighborhood(
                    self.pos, moore=self.model.reproduction_spread_moore, include_center=False, radius=self.reproduction_radius
                )
                # shuffeling the positions
                self.model.random.shuffle(possible_postitions)

                for position in possible_postitions:
                    # checking if the position is already occupied
                    if len(self.model.grid.get_cell_list_contents([position])) <= self.max_num_bacteria_in_cell:
                        new_position = position
                        break
                    else:
                        # this is only needed if there are no good positions, so new_position is defined
                        new_position = None

            else:
                # own position is good for a new cell
                new_position = self.pos

            # if all possible positions already contain max_num_bacteria_in_cell, reproduction is canceled
            if new_position != None:

                # creating and placing new bacteria
                new_bacteria = Type_a_1(self.model.next_id(), self.model, new_position)
                self.model.grid.place_agent(new_bacteria, new_position)
                self.model.schedule.add(new_bacteria)

        # has_eaten reset
        # if all neighboring positions are occupied, no new cell will be created and has_eaten will be reset anyway 
        # this was a good was to control the spread, but can be changed if you wish so
        self.has_eaten = False


    # cannot die at the moment
    # function and code is kept here, for easier customization
    def die(self):
        return
        #if self.random.random() < self.dying_chance:
        #    self.model.grid.remove_agent(self)
        #    self.model.schedule.remove(self)


    # dont know if the antibiotica is a stress reaction or a normal function
    # i think its easier to change it from this to a normal function, than the other way around
    def stress_reaction(self):

        # spread antibiotica in all neighboring cells
        neighboring_cells = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True, radius=self.stress_radius
        )

        # add antibiotica up, maybe this should be limited, as now it is like unlimited
        for cell in neighboring_cells:
            soil = self.model.grid.get_cell_list_contents([cell])[0]

            # create or add antibiotica
            if 'Type_a_2' in soil.antibiotics:
                soil.antibiotics['Type_a_2'] += 1
            else:
                soil.antibiotics['Type_a_2'] = 1 

### PREY

class Type_a_2(mesa.Agent):

    def __init__(self, unique_id, model, pos, mass):
        super().__init__(unique_id, model)

        ##### Ilya Additions:
        self.nutrient_uptake_ratio = avoid_identical_clones(0.25) # Reference paper
        self.maintenance = 0.1 # Reference paper. Units of energy that a unit of mass requieres per each time step
        self.energy_yield = 0.15 # Reference paper. Amount of energy that a unit of nutrient provides
        self.avaliability = 0.15 # Reference paper. Local avaliability of nutrients in a spatial cell for each bacterium
        self.energy_netto = 0 # Netto energy produced by bacteria during eating. If positive -> bacterium acquires mass, if negative -> shrinks
        self.mass = avoid_identical_clones(mass) 

        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # spreads the dying, to not create big bumps in the graph
        # example: average 40 turns --> 1/40 = 0.025
        self.dying_chance = 0.025
        # acts as health of the bacteria
        self.sturdiness = 1
        # limits the number of bacteria in a single cell for performance and better spreading
        self.max_num_bacteria_in_cell = 2
        # if no cell with less than self.max_num_bacteria_in_cell is found, reproduction will not take place
        self.reproduction_radius = 2
        # chance to spread when self.max_num_bacteria_in_cell is not reached, to fasten the spread
        self.random_spread_chance = 0.1
        # if True it wont spread on fields containing antibiotics against it
        # False creates a bacteria free zone between type_a_1 and type_a_2
        self.spread_in_antibiotics = False
        # nutrition and antibiotics need to be in the respective dict in the Soil object
        self.nutrition_list = ["iron"]
        self.antibiotics_list = ["Type_a_2"] # is created dynamically by type_a_1
        
        ################################
        ################################
        ################################

        self.pos = pos
        self.age = 0
        self.has_eaten = False
        
        # doesnt do anything when being eaten
        self.is_eaten = False


    # Wird bei jedem Durchgang aufgerufen
    def step(self):

        self.age += 1
        
        # if bacteria is eaten by another thing, it doesnt do anything (it will be killed by the other party)
        if not self.is_eaten:
            self.eat() 
            self.reproduce()
            self.die()


    # eat nutrients from soil   
    def eat(self):
        # get soil
        soil = self.model.grid.get_cell_list_contents([self.pos])[0]
        max_individual_uptake = self.mass * self.nutrient_uptake_ratio

        # if there are nutrients, first nutrient on nutrition_list gets consumed
        for nutrient in self.nutrition_list:
            # look if consumable nutrients in soil
            if nutrient in soil.nutrients and soil.nutrients[nutrient] > 0:
               
                max_possible_consumption = self.avaliability * soil.nutrients[nutrient] # the biggest amount each bacterium can consume

                if max_possible_consumption >= max_individual_uptake:
                    actual_consumption = max_individual_uptake # make sure that bacteria does not consume more nutrients than its individual consumption upper bounf
                else: 
                    actual_consumption = max_possible_consumption

                # subract nutrient and set has_eaten
                soil.nutrients[nutrient] -= actual_consumption
                self.has_eaten = True
                
                produced_energy = self.energy_yield * actual_consumption # convert the consumed nutrients into energy
                survival_energy = self.maintenance * self.mass # the energy that bacteria needs to survive
                self.energy_netto = produced_energy - survival_energy
                

                if self.energy_netto >= 0:
                    self.mass += self.energy_netto / 2 # Reference paper. If there is some avalaible energy, bacterium will convert half of it into mass
                else: 
                    self.mass = 0.9 * self.mass # Reference paper. If the netto energy balance is negative -> bacteria does not cover its maintenance -> shrinks 10%


                break
                


    def reproduce(self):

        if self.has_eaten:
            # Wenn bereits mehr als max_num_bacteria_in_cell Bakteriean auf einem Feld sind, oder Zufällig random_spread_chance
            if len(self.model.grid.get_cell_list_contents([self.pos])) > self.max_num_bacteria_in_cell or self.random.random() < self.random_spread_chance:
                
                # if it spreads, we randomly look for a position in the neighborhood
                possible_postitions = self.model.grid.get_neighborhood(
                    self.pos, moore=self.model.reproduction_spread_moore, include_center=False, radius=self.reproduction_radius
                )
                 # shuffeling the positions
                self.model.random.shuffle(possible_postitions)

                # checking if the position is already occupied
                for position in possible_postitions:
                    pos_contents = self.model.grid.get_cell_list_contents([position])
                    if len(pos_contents) <= self.max_num_bacteria_in_cell:
                        # if it can spread in antibiotics
                        # creates different outcomes
                        if not self.spread_in_antibiotics:
                            # spread not possible if antibiotic is in soil, next position will be checked
                            for antibiotic in self.antibiotics_list:
                                if antibiotic in pos_contents[0].antibiotics and pos_contents[0].antibiotics[antibiotic] > 0:
                                    new_position = None
                                    continue
                        new_position = position
                        break
                    else:
                        # this is only needed if there are no good positions, so new_position is defined
                        new_position = None

            else:
                # own position is good for a new cell
                new_position = self.pos

            # if all possible positions already contain max_num_bacteria_in_cell, reproduction is canceled
            if new_position != None:

                # creating and placing new bacteria
                new_bacteria = Type_a_2(self.model.next_id(), self.model, new_position, self.mass / 2)
                self.model.grid.place_agent(new_bacteria, new_position)
                self.model.schedule.add(new_bacteria)

        # has_eaten reset
        # if all neighboring positions are occupied, no new cell will be created and has_eaten will be reset anyway 
        # this was a good was to control the spread, but can be changed if you wish so
        self.has_eaten = False


    # dies if its on the same field as soil that contains an antibiotic from antibiotics_list
    def die(self):
        soil = self.model.grid.get_cell_list_contents([self.pos])[0]
        for antibiotic in self.antibiotics_list:

            # check for antibiotic
            if antibiotic in soil.antibiotics and soil.antibiotics[antibiotic] > 0:
                # die
                soil.antibiotics[antibiotic] -= 1
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)


        #if self.random.random() < self.dying_chance:
        #    self.model.grid.remove_agent(self)
        #    self.model.schedule.remove(self)

### DATA COLLECTOR

def get_num_bacteria_per_type(model, bacteria_type):
    bacteria = [a for a in model.schedule.agents if isinstance(a, bacteria_type)]
    return len(bacteria)

### MODEL

class Microbiome(mesa.Model):
    """A model with some number of agents."""
    # EVERYTHING WITH FIVE HASHTAGS IS RELATED TO INITIAL MESA SCAFFOLD AND COULD BE USEFULL IN THE FUTURE

    def __init__(self, num_type_a_1, num_type_a_2 ,is_torus, grid_height, grid_width, avrg_mass_num_type_a_2 = 280):
        # mass is 280 femtogram, which is weight from average bacteria; 

        ################################
        ### CUSTOMIZABLE VARIABLES
        ################################
        # grid_width and grid_height also need to be changed in server.py for visualisation:
        # canvas_element = mesa.visualization.CanvasGrid(bacteria_portrayal, self.grid_width, self.grid_height, 500, 500)
        self.grid_width = grid_width
        self.grid_height = grid_height
        # decides after how many turns the random direction of the type_d swarms changes
        # prevents the swarm from going back and forth 
        # done in the model for the whole swarm, so it doesnt spread
        self.swarm_direction_turns = 10
        # decides if the swarm moves in percentage 0 = 0%, 1 = 100% --> 1 means swarm moves every time
        # done in the model for the whole swarm, so it doesnt spread
        self.swarm_chance_move = 1
        # stops reproduction after population reaches a limit

        ##### REMOVED THE UPPER BOUND FOR POPULATIONS

        ##### self.type_a_population_limit = type_a_population_limit

        ##### self.type_d_population_limit = type_d_population_limit
        # reproduction spread pattern, if True includes all 8 surrounding squares, False means only up/down/left/right
        self.reproduction_spread_moore = True
        ################################
        ################################
        ################################

        self.running = True
        self.current_id = 1
        self.step_num = 1
        self.directions = ["left", "right", "up", "down"]

        # Type d moves in Swarms
        ##### self.swarm_direction = []
        ##### self.swarm_target = []

        ##### REMOVED THE UPPER BOUND FOR POPULATIONS

        ##### self.reproduction_stop_a_1 = False
        ##### self.reproduction_stop_a_2 = False

        ##### self.reproduction_stop_d = False


        ##### for s in range(num_type_d):
        #####     self.swarm_direction.append(self.random.choice(self.directions))
        #####     self.swarm_target.append([])

        self.swarm_move = True

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
        for i in range(num_type_a_1):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            a = Type_a_1(self.next_id(), self, (x, y))
            self.schedule.add(a)
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (x, y))

        # Create Type_a_2"
        for i in range(num_type_a_2):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            a = Type_a_2(self.next_id(), self, (x, y), avrg_mass_num_type_a_2)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            self.grid.place_agent(a, (x, y))


        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Type_a_1": [get_num_bacteria_per_type, [self, Type_a_1]],
                "Type_a_2": [get_num_bacteria_per_type, [self, Type_a_2]]

            }
        )


    def step(self):
        self.step_num += 1

        # reset swarm target
        ##### for idx, target in enumerate(self.swarm_target):
            # self.swarm_target[idx] = get_average_pos(target)
        #####    self.swarm_target[idx] = []


        # Type_d movement is synchronised
        ##### if self.step_num % self.swarm_direction_turns == 0:
        #####     for i in range(len(self.swarm_direction)):
        #####         self.swarm_direction[i] = self.random.choice(self.directions)

        # decides if type_d moves
        ##### if self.random.random() < self.swarm_chance_move:
        #####     self.swarm_move = True
        ##### else:
        #####     self.swarm_move = False

        # Stopping reproduction at a certain point for performance reasons
        ##### if get_num_bacteria_per_type(self, Type_d) > self.type_d_population_limit & self.type_d_population_limit != 0:
        #####     self.reproduction_stop_d = True
        ##### else:
        #####     self.reproduction_stop_d = False
        
        ##### REMOVED THE UPPER BOUND FOR POPULATIONS

        ##### if get_num_bacteria_per_type(self, Type_a_1) > self.type_a_population_limit & self.type_a_population_limit != 0:
        #####     self.reproduction_stop_a_1 = True
        ##### else:
        #####     self.reproduction_stop_a_1 = False

        ##### if get_num_bacteria_per_type(self, Type_a_2) > self.type_a_population_limit & self.type_a_population_limit != 0:
        #####     self.reproduction_stop_a_2 = True
        ##### else:
        #####     self.reproduction_stop_a_2 = False    


        # run agents
        self.datacollector.collect(self)
        self.schedule.step()