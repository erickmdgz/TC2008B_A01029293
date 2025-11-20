"""
Activity: Multi-Agent Cleaning Robot Simulation
Description: Mesa model implementation for multi-robot cleaning system with
             exclusive dock reservation. Manages grid environment, agent scheduling,
             and termination conditions for cooperative cleaning tasks.
Author: Erick Alonso Morales Dieguez
Matricula: A01029293
Date: 19/11/2024
"""

from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector

from .agent import CleanerRobot, ChargingDock, DirtyTile, Obstacle


class RoombaMultiAgentModel(Model):
    """
    Function: __init__
    Purpose: Initialize multi-agent cleaning simulation environment with configurable parameters
    Parameters:
        - numAgents: Number of cleaning robots to deploy (default: 5)
        - width: Grid width in cells (default: 25)
        - height: Grid height in cells (default: 25)
        - numDirtyCells: Initial dirty tiles to place (default: 100)
        - numObstacles: Impassable obstacles to generate (default: 20)
        - maxSteps: Maximum simulation iterations before timeout (default: 2000)
        - seed: Random seed for reproducibility (default: 42)
    Returns: None
    Note: Creates one charging dock per robot at random locations
    """
    def __init__(self, num_agents=5, width=25, height=25, num_dirty_cells=100, num_obstacles=20, max_steps=2000, seed=42):
        super().__init__(seed=seed)

        self.robotCount = num_agents
        self.roomWidth = width
        self.roomHeight = height
        self.remaining_dirt = num_dirty_cells
        self.numBlocks = num_obstacles
        self.maxIterations = max_steps
        self.seed = seed

        # Initialize grid with Moore neighborhood (8 directions)
        self.grid = OrthogonalMooreGrid([width, height], torus=False, random=self.random)

        # Simulation statistics
        self.startingDirtCount = num_dirty_cells
        self.finished = False
        self.stepsToFinish = None
        self.stepCounter = 0

        # Robot tracking
        self.cleaners = []
        self.allDocks = []  # Track all charging docks

        # Phase 1: Place obstacles
        openCells = [cell for cell in self.grid.empties.cells]
        selectedObstacleCells = self.random.sample(openCells, min(num_obstacles, len(openCells)))

        for cell in selectedObstacleCells:
            Obstacle(self, cell=cell)

        # Phase 2: Create charging docks (one per robot)
        openCells = [cell for cell in self.grid.empties.cells]
        selectedDockCells = self.random.sample(openCells, min(num_agents, len(openCells)))

        dockList = []
        for cell in selectedDockCells:
            dock = ChargingDock(self, cell=cell)
            dockList.append((dock, cell))
            self.allDocks.append(dock)

        # Phase 3: Distribute dirt
        openCells = [cell for cell in self.grid.empties.cells]
        selectedDirtyCells = self.random.sample(openCells, min(num_dirty_cells, len(openCells)))

        for cell in selectedDirtyCells:
            DirtyTile(self, cell=cell)

        # Phase 4: Deploy robots at their assigned docks
        for idx, (dock, cell) in enumerate(dockList):
            robot = CleanerRobot(self, cell=cell, home_dock=cell)
            self.cleaners.append(robot)

        # Phase 5: Initialize data collection system
        self.datacollector = DataCollector(
            model_reporters={
                "RemainingDirt": lambda m: m.remaining_dirt,
                "TotalSteps": lambda m: sum(robot.totalSteps for robot in m.cleaners),
                "AverageEnergy": lambda m: sum(robot.energy for robot in m.cleaners) / len(m.cleaners) if m.cleaners else 0,
                "MinEnergy": lambda m: min(robot.energy for robot in m.cleaners) if m.cleaners else 0,
                "MaxEnergy": lambda m: max(robot.energy for robot in m.cleaners) if m.cleaners else 0,
                "RobotsCharging": lambda m: sum(1 for robot in m.cleaners if robot.chargingMode),
                "DocksOccupied": lambda m: sum(1 for dock in m.allDocks if dock.isOccupied()),
                "DocksAvailable": lambda m: sum(1 for dock in m.allDocks if not dock.isOccupied()),
                "RobotsLowEnergy": lambda m: sum(1 for robot in m.cleaners if robot.energy < 20),
                "CleaningProgress": lambda m: ((m.startingDirtCount - m.remaining_dirt) / m.startingDirtCount * 100) if m.startingDirtCount > 0 else 100
            }
        )

        self.running = True

    """
    Function: getDockAvailability
    Purpose: Calculate current charging dock occupation statistics
    Parameters: None
    Returns: Dictionary with keys 'total', 'occupied', 'available'
    Note: Used for monitoring system performance and bottlenecks
    """
    def getDockAvailability(self):
        totalDocks = len(self.allDocks)
        occupiedDocks = sum(1 for dock in self.allDocks if dock.isOccupied())
        availableDocks = totalDocks - occupiedDocks

        return {
            'total': totalDocks,
            'occupied': occupiedDocks,
            'available': availableDocks
        }

    """
    Function: step
    Purpose: Execute one iteration of the simulation for all agents
    Parameters: None
    Returns: None
    Note: Checks termination conditions (max steps, completion, all robots dead)
    Complexity: O(n) where n is number of robots
    """
    def step(self):
        self.stepCounter += 1

        # Termination condition 1: Maximum iterations reached
        if self.stepCounter >= self.maxIterations:
            self.running = False
            self.datacollector.collect(self)
            return

        # Execute all robots in randomized order (prevents bias)
        robotOrder = self.random.sample(self.cleaners, len(self.cleaners))
        for robot in robotOrder:
            robot.step()

        # Collect data after all agents have stepped
        self.datacollector.collect(self)

        # Termination condition 2: All dirt cleaned
        if self.remaining_dirt == 0 and not self.finished:
            self.finished = True
            self.stepsToFinish = self.stepCounter
            self.running = False

        # Termination condition 3: All robots out of energy
        allStuck = True
        for robot in self.cleaners:
            # Robot is operational if has energy or is charging
            if robot.energy > 0 or robot.onAnyDock():
                allStuck = False
                break

        if allStuck:
            self.running = False
