# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    # Rule table for 1D cellular automaton
    ruleTable = {
        "111": 0, "110": 1, "101": 0,
        "100": 1, "011": 1, "010": 0,
        "001": 1, "000": 0
    }

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents

    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self, state_snapshot):
        """Compute the cell state based on the three neighbors in the row above.
        Uses 1D cellular automaton rules with the rule table.

        Args:
            state_snapshot: Immutable dictionary mapping (x, y) -> state from previous step
        """
        # Get grid dimensions
        x, y = self.x, self.y
        width = self.model.grid.dimensions[0]
        height = self.model.grid.dimensions[1]

        # Read states EXCLUSIVELY from the snapshot (previous step's state)
        # With torus=True, the grid wraps around, so we handle coordinates with modulo

        # Calculate neighbor positions with wrap-around (toroidal topology)
        left_x = (x - 1) % width
        center_x = x
        right_x = (x + 1) % width
        neighbor_y = (y + 1) % height

        # Get states from the snapshot
        left_state = state_snapshot.get((left_x, neighbor_y), self.DEAD)
        center_state = state_snapshot.get((center_x, neighbor_y), self.DEAD)
        right_state = state_snapshot.get((right_x, neighbor_y), self.DEAD)

        # Create the key for the rule table
        key = f"{left_state}{center_state}{right_state}"

        # Apply the rule
        self._next_state = self.ruleTable.get(key, self.DEAD)

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
