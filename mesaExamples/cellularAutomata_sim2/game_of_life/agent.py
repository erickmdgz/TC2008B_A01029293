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

    def determine_state(self):
        """Compute the cell state based on the three neighbors in the row above.
        Uses 1D cellular automaton rules with the rule table.
        """
        # Get grid height
        height = self.model.grid.dimensions[1]

        # If this is the top row (y=height-1), don't change state
        if self.y == height - 1:
            self._next_state = self.state
            return

        # Get the three neighbors from the row above: left, center, right
        x, y = self.x, self.y
        width = self.model.grid.dimensions[0]

        # Get positions of the three neighbors above (with wrapping for torus)
        left_pos = ((x - 1) % width, y + 1)
        center_pos = (x, y + 1)
        right_pos = ((x + 1) % width, y + 1)

        # Get the states of the three neighbors
        left_cell = self.model.grid[left_pos]
        center_cell = self.model.grid[center_pos]
        right_cell = self.model.grid[right_pos]

        # Get agents at those positions
        left_agents = left_cell.agents
        center_agents = center_cell.agents
        right_agents = right_cell.agents

        # Get states (default to DEAD if no agent)
        left_state = left_agents[0].state if left_agents else self.DEAD
        center_state = center_agents[0].state if center_agents else self.DEAD
        right_state = right_agents[0].state if right_agents else self.DEAD

        # Create the key for the rule table
        key = f"{left_state}{center_state}{right_state}"

        # Apply the rule
        self._next_state = self.ruleTable.get(key, self.DEAD)

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
