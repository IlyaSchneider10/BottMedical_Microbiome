import mesa

from Model_Ilya_Play_Area_Minimized import Microbiome, Soil, Type_a_1, Type_a_2

# EVERYTHING WITH FIVE HASHTAGS IS RELATED TO INITIAL MESA SCAFFOLD AND COULD BE USEFULL IN THE FUTURE

# Colors for the bacteria
##### COLOR_TYPE_D = "#E64A45"
COLOR_TYPE_A_1 = "#3D4C53"
COLOR_TYPE_A_2 = "#9FBF8C"


def bacteria_portrayal(agent):
    #if agent is None or isinstance(agent, Soil):
    #    return

    portrayal = {}
    # update portrayal characteristics for each Person object
    portrayal["Shape"] = "circle"
    portrayal["r"] = 0.5
    portrayal["Layer"] = 1
    portrayal["Filled"] = "true"

    # set agent color based on savings and loans
    if isinstance(agent, Type_a_1):
    	color=COLOR_TYPE_A_1
    elif isinstance(agent, Type_a_2):
        color=COLOR_TYPE_A_2    
    # showing the antibiotic type_a_2
    elif isinstance(agent, Soil):
        if 'Type_a_2' in agent.antibiotics and agent.antibiotics['Type_a_2'] > 0:        
            portrayal["r"] = 1
            color="#FF7777"
            portrayal["Layer"] = 0
        else:
            color = "WHITE"

    portrayal["Color"] = color

    return portrayal

# dictionary of user settable parameters - these map to the model __init__ parameters
model_params = {

    ##### REMOVED THE SLIDER FOR UPPER BOUND OF POPULATIONS

    ##### "STATIC_TEXT1": mesa.visualization.StaticText('<h4>Type A</h4> (Staphylococcus aureus)'),
    ##### "type_a_population_limit": mesa.visualization.Slider(
    #####    "Type_a Population Limit", 1000, 0, 10000, description="0 means no Limit"
    ##### ),
    "STATIC_TEXT2": mesa.visualization.StaticText('<br><h4>Type A 1 and Type A 2</h4> Typ A 1 can in proximity to Typ A 2 secrete antibiotica against it.'),
    "num_type_a_1": mesa.visualization.Slider(
        "Type A 1 strating population", 4, 0, 100, description="Randomly distributed"
    ),
    "num_type_a_2": mesa.visualization.Slider(
        "Type A 2 strating population", 30, 0, 100, description="Randomly distributed"
    ),
    "STATIC_TEXT3": mesa.visualization.StaticText('<br><h4>Immediate killing</h4> If True the predator kills the pray immediately with a set up agressiveness. If False reduces netto energy of bacteria by a set up agressiveness.'),
    "immediate_killing": mesa.visualization.Checkbox(
        "Immediate killing", False, description=""
    ),
    "STATIC_TEXT5": mesa.visualization.StaticText('<br><h4>Grid</h4> Torus grid connects the opposite sides of the simualtion grid.'),
    "is_torus": mesa.visualization.Checkbox(
        "Torus", False, description=""
    ),
    "grid_width": mesa.visualization.Slider(
        "Grid width", 25, 0, 100, description=""
    ),
    "grid_height": mesa.visualization.Slider(
        "Grid height", 25, 0, 100, description=""
    )
}

# set the portrayal function and size of the canvas for visualization
canvas_element = mesa.visualization.CanvasGrid(bacteria_portrayal, 25, 25, 500, 500)

# Namen der Labels müssen gleich sein wie im DataCollector im model
chart_element = mesa.visualization.ChartModule(
    [
        {"Label": "Type_a_1", "Color": COLOR_TYPE_A_1},
        {"Label": "Type_a_2", "Color": COLOR_TYPE_A_2},
    ]
)

server = mesa.visualization.ModularServer(
    Microbiome,
    [canvas_element, chart_element],
    "Microbiome",
    model_params=model_params
)