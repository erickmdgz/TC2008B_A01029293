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

        # Place a cell at each location
        # Only the top row (y=height-1) is initialized randomly
        # All other rows start as DEAD
        for cell in self.grid.all_cells:
            y_coord = cell.coordinate[1]
            if y_coord == height - 1:
                # Top row: random initialization
                init_state = (
                    Cell.ALIVE
                    if self.random.random() < initial_fraction_alive
                    else Cell.DEAD
                )
            else:
                # All other rows start DEAD
                init_state = Cell.DEAD

            Cell(self, cell, init_state=init_state)

        # Track which row we're currently computing (start from second row from top)
        self.current_row = height - 2
        self.running = True

    def step(self):
        """Perform the model step row by row from top to bottom:

        - Process only the current row based on the row above it
        - Move to the next row down for the next step
        """
        # If we've processed all rows, stop
        if self.current_row < 0:
            self.running = False
            return

        # Get all cells in the current row
        width = self.grid.dimensions[0]
        current_row_cells = []

        for x in range(width):
            cell_pos = self.grid[(x, self.current_row)]
            if cell_pos.agents:
                current_row_cells.append(cell_pos.agents[0])

        # Determine and assume state for all cells in the current row
        for cell in current_row_cells:
            cell.determine_state()

        for cell in current_row_cells:
            cell.assume_state()

        # Move to the next row down
        self.current_row -= 1
