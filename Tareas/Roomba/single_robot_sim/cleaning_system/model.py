from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector

from .agent import CleanerRobot, ChargingDock, DirtyTile, Obstacle

class RoombaCleaningModel(Model):
    def __init__(self, width=25, height=25, num_dirty_cells=50, num_obstacles=20, max_steps=1000, seed=42):
        super().__init__(seed=seed)

        self.room_width = width
        self.room_height = height
        self.remaining_dirt = num_dirty_cells
        self.num_blocks = num_obstacles
        self.max_iterations = max_steps
        self.seed = seed

        # Create grid
        self.grid = OrthogonalMooreGrid([width, height], torus=False, random=self.random)

        # Stats
        self.starting_dirt_count = num_dirty_cells
        self.finished = False
        self.steps_to_finish = None
        self.moves_made = 0
        self.step_counter = 0

        # Place charging dock at (1, 1)
        dock_location = self.grid[(1, 1)]
        self.charging_dock = ChargingDock(self, cell=dock_location)

        # Add obstacles
        open_cells = [cell for cell in self.grid.empties.cells if cell.coordinate != (1, 1)]
        selected_obstacle_cells = self.random.sample(open_cells, min(num_obstacles, len(open_cells)))

        for cell in selected_obstacle_cells:
            Obstacle(self, cell=cell)

        # Add dirt
        open_cells = [cell for cell in self.grid.empties.cells if cell.coordinate != (1, 1)]
        selected_dirty_cells = self.random.sample(open_cells, min(num_dirty_cells, len(open_cells)))

        for cell in selected_dirty_cells:
            DirtyTile(self, cell=cell)

        # Create robot
        self.cleaner = CleanerRobot(self, cell=dock_location, home_dock=dock_location)

        # Initialize data collection system
        self.datacollector = DataCollector(
            model_reporters={
                "RemainingDirt": lambda m: m.remaining_dirt,
                "TotalSteps": lambda m: m.cleaner.total_steps,
                "RobotEnergy": lambda m: m.cleaner.energy,
                "IsCharging": lambda m: 1 if m.cleaner.charging_mode else 0,
                "DockOccupied": lambda m: 1 if m.charging_dock.is_occupied() else 0,
                "CleaningProgress": lambda m: ((m.starting_dirt_count - m.remaining_dirt) / m.starting_dirt_count * 100) if m.starting_dirt_count > 0 else 100
            }
        )

        self.running = True

    def step(self):
        # Run one iteration
        self.step_counter += 1

        # Check max iterations
        if self.step_counter >= self.max_iterations:
            self.running = False
            self.datacollector.collect(self)
            return

        # Execute robot step
        self.cleaner.step()

        # Update moves
        self.moves_made = self.cleaner.total_steps

        # Collect data after agent has stepped
        self.datacollector.collect(self)

        # Check if finished
        if self.remaining_dirt == 0 and not self.finished:
            self.finished = True
            self.steps_to_finish = self.step_counter
            self.running = False

        # Check if stuck
        no_energy = self.cleaner.energy <= 0
        not_on_dock = not self.cleaner.on_charging_dock()
        if no_energy and not_on_dock:
            self.running = False
