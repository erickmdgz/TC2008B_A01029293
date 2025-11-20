"""
Activity: Multi-Agent Cleaning Robot Simulation
Description: Implementation of autonomous cleaning robots with exclusive charging
             dock reservation system. Robots navigate a grid environment, clean
             dirty tiles, manage energy levels, and coordinate dock usage to avoid
             conflicts in multi-agent scenarios.
Author: Erick Alonso Morales Dieguez
Matricula: A01029293
Date: 19/11/2024
"""

from mesa.discrete_space import CellAgent, FixedAgent
from collections import deque


class CleanerRobot(CellAgent):
    """
    Function: __init__
    Purpose: Initialize a cleaning robot agent with energy management and navigation capabilities
    Parameters:
        - model: Reference to the Mesa model instance
        - cell: Initial cell position in the grid
        - home_dock: Primary charging dock for this robot
    Returns: None
    Note: Robot starts with full energy (100) and no reserved dock
    """
    def __init__(self, model, cell, home_dock):
        super().__init__(model)
        self.cell = cell
        self.energy = 100
        self.totalSteps = 0
        self.homeDock = home_dock
        self.chargingMode = False
        self.pathHome = []
        self.reservedDock = None  # Currently reserved dock (if any)
        self.waitingForDock = False  # Flag for dock queue behavior

    """
    Function: needsRecharge
    Purpose: Determine if robot requires energy replenishment
    Parameters: None
    Returns: Boolean indicating if recharge is needed
    Note: Threshold set at 20% energy when not on any charging dock
    """
    def needsRecharge(self):
        if self.energy < 20 and not self.onAnyDock():
            return True
        return False

    """
    Function: onAnyDock
    Purpose: Check if robot is currently positioned on any charging dock
    Parameters: None
    Returns: Boolean indicating dock presence at current cell
    Note: Scans all agents in current cell for ChargingDock instances
    """
    def onAnyDock(self):
        docksHere = [agent for agent in self.cell.agents if isinstance(agent, ChargingDock)]
        if len(docksHere) > 0:
            return True
        return False

    """
    Function: onChargingDock
    Purpose: Alias method for dock detection (compatibility)
    Parameters: None
    Returns: Boolean from onAnyDock()
    Note: Maintained for backward compatibility with existing code
    """
    def onChargingDock(self):
        return self.onAnyDock()

    """
    Function: getCurrentDock
    Purpose: Retrieve the dock object at robot's current position
    Parameters: None
    Returns: ChargingDock instance if present, None otherwise
    Note: Returns first dock found (should only be one per cell)
    """
    def getCurrentDock(self):
        docksHere = [agent for agent in self.cell.agents if isinstance(agent, ChargingDock)]
        if len(docksHere) > 0:
            return docksHere[0]
        return None

    """
    Function: restoreEnergy
    Purpose: Charge robot battery when positioned on available charging dock
    Parameters: None
    Returns: None
    Note: Charges at rate of 5 points per step, releases dock when full
    Complexity: O(1)
    """
    def restoreEnergy(self):
        if not self.onAnyDock():
            self.chargingMode = False
            if self.reservedDock is not None:
                self.reservedDock.releaseDock()
                self.reservedDock = None
            return

        currentDock = self.getCurrentDock()

        # Attempt to reserve dock if not already reserved
        if self.reservedDock is None:
            if currentDock.isOccupied() and currentDock.currentUser != self:
                # Dock occupied by another robot - must leave
                self.chargingMode = False
                self.moveAwayFromDock()
                return
            else:
                # Reserve this dock
                currentDock.reserveDock(self)
                self.reservedDock = currentDock

        if self.energy >= 100:
            # Fully charged - release dock
            self.chargingMode = False
            if self.reservedDock is not None:
                self.reservedDock.releaseDock()
                self.reservedDock = None
            return

        self.energy = min(100, self.energy + 5)
        self.chargingMode = True

    """
    Function: moveAwayFromDock
    Purpose: Move robot to adjacent cell when dock is unavailable
    Parameters: None
    Returns: None
    Note: Used when robot arrives at occupied dock
    """
    def moveAwayFromDock(self):
        availableCells = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(agent, (Obstacle, CleanerRobot)) for agent in cell.agents)
        )

        if len(availableCells.cells) > 0:
            self.cell = availableCells.select_random_cell()
            self.waitingForDock = True

    """
    Function: cleanCurrentPosition
    Purpose: Remove dirt from current cell if present
    Parameters: None
    Returns: Boolean indicating if cleaning action was performed
    Note: Consumes 1 energy point per cleaning action
    Complexity: O(n) where n is agents per cell (typically small)
    """
    def cleanCurrentPosition(self):
        dirtHere = [agent for agent in self.cell.agents if isinstance(agent, DirtyTile)]
        if not dirtHere:
            return False

        if self.energy <= 0:
            return False

        for dirt in dirtHere:
            dirt.remove()

        self.energy -= 1
        self.model.remaining_dirt -= 1
        return True

    """
    Function: findNearestAvailableDock
    Purpose: Locate closest charging dock that is not currently occupied
    Parameters: None
    Returns: Cell containing available dock, or None if all occupied
    Note: Uses BFS traversal to find minimum distance path
    Complexity: O(V + E) where V is cells, E is edges in grid graph
    """
    def findNearestAvailableDock(self):
        queue = deque()
        queue.append((self.cell, 0))
        visited = set()
        visited.add(self.cell)

        while len(queue) > 0:
            current, distance = queue.popleft()

            # Check for available dock at current cell
            docksHere = [agent for agent in current.agents if isinstance(agent, ChargingDock)]
            if len(docksHere) > 0:
                dock = docksHere[0]
                # Only return if dock is available or already reserved by this robot
                if not dock.isOccupied() or dock.currentUser == self:
                    return current

            # Expand search to neighbors
            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, Obstacle) for agent in cell.agents)
            )

            for nextCell in neighbors.cells:
                if nextCell in visited:
                    continue
                visited.add(nextCell)
                queue.append((nextCell, distance + 1))

        return None

    """
    Function: findPathHome
    Purpose: Calculate shortest path to nearest available charging dock
    Parameters: None
    Returns: List of cells representing path (excluding current position)
    Note: Updates targetDock and clears path if dock becomes occupied
    Complexity: O(V + E) BFS traversal
    """
    def findPathHome(self):
        nearestDockCell = self.findNearestAvailableDock()

        if nearestDockCell is None:
            # No available docks found
            self.waitingForDock = True
            return []

        if nearestDockCell == self.cell:
            return []

        # BFS pathfinding to target dock
        queue = deque()
        queue.append((self.cell, [self.cell]))
        visited = set()
        visited.add(self.cell)

        while len(queue) > 0:
            current, path = queue.popleft()

            if current == nearestDockCell:
                return path[1:]

            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, Obstacle) for agent in cell.agents)
            )

            for nextCell in neighbors.cells:
                if nextCell in visited:
                    continue
                visited.add(nextCell)
                newPath = path + [nextCell]
                queue.append((nextCell, newPath))

        return []

    """
    Function: moveTowardsDock
    Purpose: Execute one step of movement along path to charging dock
    Parameters: None
    Returns: Boolean indicating if movement was successful
    Note: Recalculates path if empty, consumes 1 energy per move
    """
    def moveTowardsDock(self):
        if len(self.pathHome) == 0:
            self.pathHome = self.findPathHome()

        if len(self.pathHome) == 0:
            # No path available - try low power mode
            if self.energy > 0:
                self.energy -= 0.5  # Reduced consumption while waiting
            return False

        if self.energy <= 0:
            return False

        destination = self.pathHome.pop(0)

        # Check if destination has another robot
        robotsThere = [agent for agent in destination.agents if isinstance(agent, CleanerRobot)]
        if len(robotsThere) > 0:
            # Path blocked - recalculate next step
            self.pathHome = []
            return False

        self.cell = destination
        self.energy -= 1
        self.totalSteps += 1
        return True

    """
    Function: exploreAndClean
    Purpose: Navigate environment seeking dirty tiles to clean
    Parameters: None
    Returns: Boolean indicating if movement/action occurred
    Note: Prioritizes dirty neighbors over random exploration
    Complexity: O(n) where n is neighborhood size (8 for Moore)
    """
    def exploreAndClean(self):
        if self.energy <= 0:
            return False

        # Priority 1: Move to dirty adjacent cells
        dirtyCells = self.cell.neighborhood.select(
            lambda cell: any(isinstance(agent, DirtyTile) for agent in cell.agents) and
                        not any(isinstance(agent, (Obstacle, CleanerRobot)) for agent in cell.agents)
        )

        if len(dirtyCells.cells) > 0:
            self.cell = dirtyCells.select_random_cell()
            self.energy -= 1
            self.totalSteps += 1
            return True

        # Priority 2: Random exploration
        availableCells = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(agent, (Obstacle, CleanerRobot)) for agent in cell.agents)
        )

        if len(availableCells.cells) > 0:
            self.cell = availableCells.select_random_cell()
            self.energy -= 1
            self.totalSteps += 1
            return True

        return False

    """
    Function: step
    Purpose: Execute one timestep of robot behavior using priority-based decision tree
    Parameters: None
    Returns: None
    Note: Priority order: Charging > Recharge navigation > Cleaning > Exploration
    """
    def step(self):
        # Release dock reservation if robot has one but is not on a dock
        if self.reservedDock is not None and not self.onAnyDock():
            self.reservedDock.releaseDock()
            self.reservedDock = None
            self.chargingMode = False

        # Priority 1: Charge if on dock and not full
        if self.onAnyDock() and self.energy < 100:
            self.restoreEnergy()
            return

        # Priority 2: Navigate to dock if low energy
        if self.needsRecharge():
            self.moveTowardsDock()
            return

        # Priority 3: Clean current position if dirty
        if self.cleanCurrentPosition():
            return

        # Priority 4: Explore and search for dirt
        self.exploreAndClean()


class ChargingDock(FixedAgent):
    """
    Function: __init__
    Purpose: Initialize charging dock with exclusive access control
    Parameters:
        - model: Reference to the Mesa model instance
        - cell: Fixed cell position in the grid
    Returns: None
    Note: Docks start unoccupied and available for reservation
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.currentUser = None  # Robot currently using this dock
        self.isAvailable = True  # Quick availability flag

    """
    Function: reserveDock
    Purpose: Assign exclusive dock access to a specific robot
    Parameters:
        - robot: CleanerRobot instance requesting reservation
    Returns: Boolean indicating reservation success
    Note: Only one robot can reserve dock at a time
    """
    def reserveDock(self, robot):
        if self.currentUser is None:
            self.currentUser = robot
            self.isAvailable = False
            return True
        return False

    """
    Function: releaseDock
    Purpose: Free dock from current reservation, making it available
    Parameters: None
    Returns: None
    Note: Should be called when robot completes charging or leaves
    """
    def releaseDock(self):
        self.currentUser = None
        self.isAvailable = True

    """
    Function: isOccupied
    Purpose: Check if dock is currently reserved by any robot
    Parameters: None
    Returns: Boolean indicating occupation status
    """
    def isOccupied(self):
        return self.currentUser is not None

    """
    Function: step
    Purpose: Execute dock behavior per simulation timestep
    Parameters: None
    Returns: None
    Note: Docks are passive - no active behavior required
    """
    def step(self):
        pass


class DirtyTile(FixedAgent):
    """
    Function: __init__
    Purpose: Initialize a dirty tile marker in the environment
    Parameters:
        - model: Reference to the Mesa model instance
        - cell: Fixed cell position containing dirt
    Returns: None
    Note: Represents cleanable dirt in simulation
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    """
    Function: step
    Purpose: Execute tile behavior per simulation timestep
    Parameters: None
    Returns: None
    Note: Dirty tiles are passive until cleaned by robots
    """
    def step(self):
        pass


class Obstacle(FixedAgent):
    """
    Function: __init__
    Purpose: Initialize an impassable obstacle in the grid
    Parameters:
        - model: Reference to the Mesa model instance
        - cell: Fixed cell position of obstacle
    Returns: None
    Note: Blocks robot movement and pathfinding
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    """
    Function: step
    Purpose: Execute obstacle behavior per simulation timestep
    Parameters: None
    Returns: None
    Note: Obstacles are static environment elements
    """
    def step(self):
        pass
