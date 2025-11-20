"""
Activity: Multi-Agent Cleaning Robot Simulation
Description: SolaraViz visualization interface for multi-robot cleaning system.
             Provides interactive controls for simulation parameters and real-time
             visualization of robot behavior, energy levels, and cleaning progress.
Author: Erick Alonso Morales Dieguez
Matricula: A01029293
Date: 19/11/2024
"""

from cleaning_fleet.agent import CleanerRobot, ChargingDock, DirtyTile, Obstacle
from cleaning_fleet.model import RoombaMultiAgentModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle


"""
Function: getAgentStyle
Purpose: Define visual appearance for each agent type in the simulation
Parameters:
    - agent: Agent instance to style (CleanerRobot, ChargingDock, etc.)
Returns: AgentPortrayalStyle object with color, marker, and size properties
Note: Robot color indicates energy level - Red (charging), Green (>50%),
      Yellow (20-50%), Orange (<20%)
"""
def getAgentStyle(agent):
    if agent is None:
        return

    style = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, CleanerRobot):
        # Energy-based color coding
        if agent.chargingMode:
            style.color = "red"  # Red while charging
        elif agent.energy > 50:
            style.color = "green"  # Green when high energy
        elif agent.energy > 20:
            style.color = "yellow"  # Yellow when medium energy
        else:
            style.color = "orange"  # Orange when low energy
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


"""
Function: setAspectRatio
Purpose: Configure matplotlib axes to display square grid cells
Parameters:
    - ax: Matplotlib axes object to configure
Returns: None
Note: Ensures grid cells render as squares rather than rectangles
"""
def setAspectRatio(ax):
    ax.set_aspect("equal")


# Simulation parameter controls
modelSettings = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num_agents": Slider("Number of cleaning agents", 5, 1, 20),
    "width": Slider("Grid width", 25, 10, 50),
    "height": Slider("Grid height", 25, 10, 50),
    "num_dirty_cells": Slider("Number of dirty cells", 100, 10, 300),
    "num_obstacles": Slider("Number of obstacles", 20, 0, 100),
    "max_steps": Slider("Maximum steps", 2000, 100, 5000),
}

# Create initial model instance
cleaningModel = RoombaMultiAgentModel(
    num_agents=modelSettings["num_agents"].value,
    width=modelSettings["width"].value,
    height=modelSettings["height"].value,
    num_dirty_cells=modelSettings["num_dirty_cells"].value,
    num_obstacles=modelSettings["num_obstacles"].value,
    max_steps=modelSettings["max_steps"].value,
    seed=modelSettings["seed"]["value"]
)

# Configure space visualization component
spaceDisplay = make_space_component(
    getAgentStyle,
    draw_grid=True,
    post_process=setAspectRatio
)

"""
Function: createPlotComponents
Purpose: Create real-time plot components for monitoring simulation metrics
Parameters: None
Returns: List of plot component objects
Note: Creates 4 plots - cleaning progress, energy management, dock usage, efficiency
"""
# Plot 1: Cleaning Progress
cleaningPlot = make_plot_component(
    {"RemainingDirt": "brown", "CleaningProgress": "lightblue"}
)

# Plot 2: Energy Management
energyPlot = make_plot_component(
    {
        "AverageEnergy": "green",
        "RobotsCharging": "yellow",
        "RobotsLowEnergy": "red"
    }
)

# Plot 3: Dock Usage
dockPlot = make_plot_component(
    {"DocksOccupied": "blue", "DocksAvailable": "lightblue"}
)

# Plot 4: System Efficiency (derived metric)
# Note: Efficiency calculated as CleaningProgress / TotalSteps ratio
efficiencyPlot = make_plot_component(
    {"TotalSteps": "purple"}
)

# Create Solara visualization page
page = SolaraViz(
    cleaningModel,
    components=[spaceDisplay, cleaningPlot, energyPlot, dockPlot, efficiencyPlot],
    model_params=modelSettings,
    name="Multi-Robot Cleaning Simulation",
)
