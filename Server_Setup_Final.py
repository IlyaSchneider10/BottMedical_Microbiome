import mesa

from Model_Ilya_Final import *

# EVERYTHING WITH FIVE HASHTAGS IS RELATED TO INITIAL MESA SCAFFOLD AND COULD BE USEFULL IN THE FUTURE

# Colors for the bacteria

COLOR_TYPE_A_1 = "#3D4C53"

COLOR_TYPE_A_2 = "#9FBF8C"


def bacteria_portrayal(agent):

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
    elif isinstance(agent, Soil):
        if 'Type_a_2_X' in agent.antibiotics and agent.antibiotics['Type_a_2_X'] > 0:        
            portrayal["r"] = 1
            color = "#F5C3C2"
            portrayal["Layer"] = 0
        else:
            color = "WHITE"

    portrayal["Color"] = color

    return portrayal

# dictionary of user settable parameters - these map to the model __init__ parameters
model_params = {

    "STATIC_TEXT2": mesa.visualization.StaticText('<br><h4>Type A 1 and Type A 2</h4> Typ A 1 can in proximity to Typ A 2 secrete antibiotica against it.'),
    "num_type_a_1": mesa.visualization.Slider(
        "Type A 1 strating population", 30, 0, 100, description="Randomly distributed"
    ),
    "num_type_a_2": mesa.visualization.Slider(
        "Type A 2 strating population", 160, 0, 250, description="Randomly distributed"
    ),
    "STATIC_TEXT3": mesa.visualization.StaticText('<br><h4>Immediate killing</h4> If True the predator kills the pray immediately with a set up agressiveness. If False reduces netto energy of bacteria by a set up agressiveness.'),
    "immediate_killing": mesa.visualization.Checkbox(
        "Immediate killing", True, description=""
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
    ),
    "aggressiveness": mesa.visualization.Slider(
        "Aggressiveness", 10, 0.0, 100, description=""
    ),
    "avrg_viability_time_type_a": mesa.visualization.Slider(
        "avrg_viability_time_type_a", 35, 0.0, 100, description=""
    )
}

# set the portrayal function and size of the canvas for visualization
canvas_element = mesa.visualization.CanvasGrid(bacteria_portrayal, 25, 25, 500, 500)

# Namen der Labels müssen gleich sein wie im DataCollector im model
chart_element = mesa.visualization.ChartModule(
    [
        {"Label": "A1_Number", "Color": COLOR_TYPE_A_1},
        {"Label": "A2_Number", "Color": COLOR_TYPE_A_2}
    ]
)

server = mesa.visualization.ModularServer(
    Microbiome,
    [canvas_element, chart_element],
    "Microbiome",
    model_params=model_params
)