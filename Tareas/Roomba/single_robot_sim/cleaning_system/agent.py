from mesa.discrete_space import CellAgent, FixedAgent
from collections import deque

class CleanerRobot(CellAgent):
    def __init__(self, model, cell, home_dock):
        super().__init__(model)
        self.cell = cell
        self.energy = 100
        self.total_steps = 0
        self.home_dock = home_dock
        self.charging_mode = False
        self.path_home = []

    def needs_recharge(self):
        # Low energy and away from dock
        if self.energy < 20 and self.cell != self.home_dock:
            return True
        return False

    def on_charging_dock(self):
        return self.cell == self.home_dock

    def restore_energy(self):
        # Charge up when on dock
        if not self.on_charging_dock():
            self.charging_mode = False
            return

        if self.energy >= 100:
            self.charging_mode = False
            return

        self.energy = min(100, self.energy + 5)
        self.charging_mode = True

    def clean_current_position(self):
        # Remove dirt from this tile
        dirt_here = [agent for agent in self.cell.agents if isinstance(agent, DirtyTile)]

        if not dirt_here:
            return False

        if self.energy <= 0:
            return False

        for dirt in dirt_here:
            dirt.remove()

        self.energy -= 1
        self.model.remaining_dirt -= 1
        return True

    def find_path_home(self):
        # BFS search to home dock
        if self.on_charging_dock():
            return []

        queue = deque()
        queue.append((self.cell, [self.cell]))
        visited = set()
        visited.add(self.cell)

        while len(queue) > 0:
            current, path = queue.popleft()

            if current == self.home_dock:
                return path[1:]

            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, Obstacle) for agent in cell.agents)
            )

            for next_cell in neighbors.cells:
                if next_cell in visited:
                    continue
                visited.add(next_cell)
                new_path = path + [next_cell]
                queue.append((next_cell, new_path))

        return []

    def move_towards_dock(self):
        # Go home one step
        if len(self.path_home) == 0:
            self.path_home = self.find_path_home()

        if len(self.path_home) == 0:
            return False

        if self.energy <= 0:
            return False

        destination = self.path_home.pop(0)
        self.cell = destination
        self.energy -= 1
        self.total_steps += 1
        return True

    def explore_and_clean(self):
        # Move around looking for dirt
        if self.energy <= 0:
            return False

        # Find dirty neighbors first
        dirty_cells = self.cell.neighborhood.select(
            lambda cell: any(isinstance(agent, DirtyTile) for agent in cell.agents) and
                        not any(isinstance(agent, (Obstacle, CleanerRobot)) for agent in cell.agents)
        )

        if len(dirty_cells.cells) > 0:
            self.cell = dirty_cells.select_random_cell()
            self.energy -= 1
            self.total_steps += 1
            return True

        # Random movement
        available_cells = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(agent, (Obstacle, CleanerRobot)) for agent in cell.agents)
        )

        if len(available_cells.cells) > 0:
            self.cell = available_cells.select_random_cell()
            self.energy -= 1
            self.total_steps += 1
            return True

        return False

    def step(self):
        # Main action loop
        if self.on_charging_dock() and self.energy < 100:
            self.restore_energy()
            return

        if self.needs_recharge():
            self.move_towards_dock()
            return

        if self.clean_current_position():
            return

        self.explore_and_clean()


class ChargingDock(FixedAgent):
    # Energy station
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass


class DirtyTile(FixedAgent):
    # Tile with dirt
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass


class Obstacle(FixedAgent):
    # Block in the grid
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass
