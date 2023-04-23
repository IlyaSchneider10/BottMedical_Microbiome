import mesa

from Model_Ilya import Microbiome, Soil, Type_a_1, Type_a_2

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
    "STATIC_TEXT2": mesa.visualization.StaticText('<br><h4>Type A 1 und Type A 2</h4>(Sub-Arten Staphylococcus aureus)<br> Typ A 1 kann Antibiotika gegen Typ A 2 absondern'),
    "num_type_a_1": mesa.visualization.Slider(
        "Type_a_1 Anfangspopulation", 1, 0, 10, description="Zufällig Verteilt"
    ),
    "num_type_a_2": mesa.visualization.Slider(
        "Type_a_2 Anfangspopulation", 1, 0, 10, description="Zufällig Verteilt"
    ),
    "STATIC_TEXT5": mesa.visualization.StaticText('<br><h4>Grid</h4> Torus: Ein Torusgitter ist ein zweidimensionales Gitter, das sich zu einem Ring formt, indem die gegenüberliegenden Ränder verbunden werden.<br>grid_width und grid_height: an der Visualisierung änder sich nichts, es wird aber nur ein Teil des Gitters verwendet'),
    "is_torus": mesa.visualization.Checkbox(
        "Torus", True, description=""
    ),
    "grid_width": mesa.visualization.Slider(
        "grid_width", 100, 0, 100, description=""
    ),
    "grid_height": mesa.visualization.Slider(
        "grid_height", 100, 0, 100, description=""
    )
}

# set the portrayal function and size of the canvas for visualization
canvas_element = mesa.visualization.CanvasGrid(bacteria_portrayal, 100, 100, 500, 500)

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