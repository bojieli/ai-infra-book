from gurobipy import Model, GRB, Env
from meshSolver import Solver, get_global_id
from var import Category, State, port_node_map
import os

WIDTH = 7
HEIGHT = 3
NUM_CELL = 3 * HEIGHT + 1 + (2 * HEIGHT + 3) * (WIDTH - 1) // 2

class PUC:
    def __init__(self, index, category, adjacent_nodes):
        self.index = index
        self.category = category
        self.adjacent_nodes = adjacent_nodes
        self.state = State.UNDEFINED
        self.result = None

    def set_state(self, state):
        self.state = state

    def __repr__(self):
        return f"PUC({self.index} | {self.state})"

class iPronics_solver:
    def __init__(self, use_env=False):
        self.link_bar_puc_map = {}
        self.link_cross_puc_map = {}
        self.puc_list = []
        self.env = None
        self.solver = None
        if use_env:
            self.env = Env(
                params={
                    "LICENSEID": int(os.getenv("LICENSEID")),
                    "WLSACCESSID": os.getenv("WLSACCESSID"),
                    "WLSSECRET": os.getenv("WLSSECRET"),
                }
            )

        for i in range(72):
            _, puc = puc2cell(i)
            self.puc_list.append(puc)
            nodes = puc.adjacent_nodes
            self.link_bar_puc_map[(nodes[0], nodes[1])] = puc
            self.link_bar_puc_map[(nodes[1], nodes[0])] = puc
            self.link_bar_puc_map[(nodes[2], nodes[3])] = puc
            self.link_bar_puc_map[(nodes[3], nodes[2])] = puc
            self.link_cross_puc_map[(nodes[0], nodes[2])] = puc
            self.link_cross_puc_map[(nodes[2], nodes[0])] = puc
            self.link_cross_puc_map[(nodes[1], nodes[3])] = puc
            self.link_cross_puc_map[(nodes[3], nodes[1])] = puc

    def clear(self):
        pass

    def solve(self, sources, drains, max_len=14):
        # return a list of PUC states, (<id>, "x") or (<id>, "=")
        if not self.env:
            model = Model("ipronics")
        else:
            model = Model("ipronics", self.env)
        sources = [port_node_map[s] for s in sources]
        drains = [port_node_map[s] for s in drains]

        solver = Solver(model, num_cell=NUM_CELL, height=HEIGHT, source=sources, drain=drains, max_len=max_len)
        # solver.show()
        try:
            solver.solve()
            link_list = solver.get_solution()
        except Exception as e:
            print(e)
            return None
        
        for link in link_list:
            puc = self.link_bar_puc_map.get(link)
            if puc:
                puc.set_state(State.BAR)
            else:
                puc = self.link_cross_puc_map.get((link[0], link[1]))
                if puc:
                    puc.set_state(State.CROSS)
                else:
                    raise f"Link not found: {link}"

        result = []
        for puc in self.puc_list:
            if puc.state != State.UNDEFINED:
                result.append((puc.index, "=" if puc.state == State.BAR else "x"))

        self.result = result
        self.solver = solver
        return result

    def show(self):
        if not self.result:
            return
        print(self.result)
        self.solver.show()
    


def get_adjacent_cell_node(puc_index, index1, index2, row_idx, category):
    starting_cell_ids = [[0, 3, 3, 7], 
                        [8, 12, 12, 16],
                        [17, 21, 21, 25], 
                        [26, 30, 30]]
    starting_cell_id = starting_cell_ids[index1][index2]
    result = []
    puc = None
    if index2 == 0:
        result = [starting_cell_id + row_idx]
        if category == Category.R:
            result.append(starting_cell_id + row_idx + (3 if index1 == 0 else 4))
            puc = PUC(puc_index, category, [result[0] * 6 + 1, result[0] * 6 + 2, result[1] * 6 + 4, result[1] * 6 + 5])
        else:
            result.append(starting_cell_id + row_idx + (4 if index1 == 0 else 5))
            puc = PUC(puc_index, category, [result[0] * 6 + 2, result[0] * 6 + 3, result[1] * 6 + 5, result[1] * 6])
    elif index2 == 1 or index2 == 3:
        result = [starting_cell_id + row_idx, starting_cell_id + row_idx + 1]
        puc = PUC(puc_index, category, [result[0] * 6 + 3, result[0] * 6 + 4, result[1] * 6 + 0, result[1] * 6 + 1])

    elif index2 == 2:
        result = [starting_cell_id + row_idx]
        if category == Category.L:
            result.append(starting_cell_id + row_idx + (5 if index1 < 3 else 4))
            puc = PUC(puc_index, category, [result[0] * 6 + 2, result[0] * 6 + 3, result[1] * 6 + 5, result[1] * 6])
        else:
            result.append(starting_cell_id + row_idx + (4 if index1 < 3 else 3))
            puc = PUC(puc_index, category, [result[0] * 6 + 1, result[0] * 6 + 2, result[1] * 6 + 4, result[1] * 6 + 5])

    return result, puc

def puc2cell(puc_index):
    index1 = puc_index // 19
    res1 = puc_index % 19
    index2 = 0
    row = 0
    category = Category.H
    if res1 < 6:
        index2 = 0
        row = res1 // 2
        category = Category.R if res1 % 2 == 0 else Category.L
    elif res1 < 9:
        index2 = 1
        row = res1 - 6
        category = Category.H
    elif res1 < 15:
        index2 = 2
        row = (res1 - 9 + 1) // 2
        category = Category.L if (res1 - 9) % 2 == 0 else Category.R
    else:
        index2 = 3
        row = res1 - 15
        category = Category.H

    return get_adjacent_cell_node(puc_index, index1, index2, row, category)


if __name__ == "__main__":
    solver = iPronics_solver()
    result = solver.solve([0, 2], [14, 12], show=True)
