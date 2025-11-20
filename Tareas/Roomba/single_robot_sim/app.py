from cleaning_system.agent import CleanerRobot, ChargingDock, DirtyTile, Obstacle
from cleaning_system.model import RoombaCleaningModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def get_agent_style(agent):
    # Visual styling for agents
    if agent is None:
        return

    style = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, CleanerRobot):
        # Energy-based coloring
        if agent.charging_mode:
            style.color = "red"
        elif agent.energy > 50:
            style.color = "green"
        elif agent.energy > 20:
            style.color = "yellow"
        else:
            style.color = "orange"
        style.marker = "o"
        style.size = 80
    elif isinstance(agent, ChargingDock):
        style.color = "blue"
        style.marker = "s"
        style.size = 100
    elif isinstance(agent, DirtyTile):
        style.color = "brown"
        style.marker = "x"
        style.size = 60
    elif isinstance(agent, Obstacle):
        style.color = "gray"
        style.marker = "s"
        style.size = 100

    return style

def set_aspect_ratio(ax):
    # Square grid
    ax.set_aspect("equal")

model_settings = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": Slider("Grid width", 25, 10, 50),
    "height": Slider("Grid height", 25, 10, 50),
    "num_dirty_cells": Slider("Number of dirty cells", 50, 10, 200),
    "num_obstacles": Slider("Number of obstacles", 20, 0, 100),
    "max_steps": Slider("Maximum steps", 1000, 100, 5000),
}

# Create model instance
cleaning_model = RoombaCleaningModel(
    width=model_settings["width"].value,
    height=model_settings["height"].value,
    num_dirty_cells=model_settings["num_dirty_cells"].value,
    num_obstacles=model_settings["num_obstacles"].value,
    max_steps=model_settings["max_steps"].value,
    seed=model_settings["seed"]["value"]
)

space_display = make_space_component(
    get_agent_style,
    draw_grid=True,
    post_process=set_aspect_ratio
)

page = SolaraViz(
    cleaning_model,
    components=[space_display],
    model_params=model_settings,
    name="Simulacion 1",
)
