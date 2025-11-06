from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell


class ConwaysGameOfLife(Model):
    """Represents the 2-dimensional array of cells in a 1D cellular automaton."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Create a new playing area of (width, height) cells."""
        super().__init__(seed=seed)

        """Grid where cells are connected to their 8 neighbors.

        Example for two dimensions:
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1),
        ]
        """
        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=True)

        # Place a cell at each location with random initialization
        # All cells are initialized randomly based on initial_fraction_alive
        for cell in self.grid.all_cells:
            init_state = (
                Cell.ALIVE
                if self.random.random() < initial_fraction_alive
                else Cell.DEAD
            )
            Cell(self, cell, init_state=init_state)

        self.running = True

    def step(self):
        """Perform synchronous update of all cells in the grid.

        Each cell determines its next state based on its three neighbors above,
        then all cells update simultaneously.
        """
        # Get all cell agents from the grid
        all_cells = []
        for cell in self.grid.all_cells:
            if cell.agents:
                all_cells.append(cell.agents[0])

        # Create immutable snapshot of current state BEFORE any calculations
        # This ensures all reads are from the previous step's state
        state_snapshot = {}
        for cell_agent in all_cells:
            state_snapshot[(cell_agent.x, cell_agent.y)] = cell_agent.state

        # Phase 1: All cells determine their next state based on the snapshot
        # No cell modifies its visible state during this phase
        for cell in all_cells:
            cell.determine_state(state_snapshot)

        # Phase 2: All cells apply their new state simultaneously
        for cell in all_cells:
            cell.assume_state()
