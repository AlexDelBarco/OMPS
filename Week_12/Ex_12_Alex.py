from gurobipy import Model, GRB, LinExpr, quicksum
import numpy as np

# Input data
load = 200  # Inflexible load (MWh)
generators = {
    "G1": {"day_ahead_cost": 75, "up_cost": 77, "down_cost": 74, "capacity": 100, "up_adj": 10, "down_adj": 10},
    "G2": {"day_ahead_cost": 5, "up_cost": 7, "down_cost": 4, "capacity": 150, "up_adj": 150, "down_adj": 150},
    "G3": {"day_ahead_cost": 80, "up_cost": 82, "down_cost": 79, "capacity": 50, "up_adj": 50, "down_adj": 50}
}
wind_scenarios = [0.6, 0.7, 0.75, 0.85]  # Normalized wind production
probabilities = [0.25, 0.25, 0.4, 0.1]  # Scenario probabilities

# Helper functions
def solve_master(day_ahead_dispatch, cuts):
    """Solves the master problem with Benders cuts."""
    master = Model("Master Problem")

    # Variables
    da_gen = master.addVars(generators.keys(), lb=0, name="day_ahead_gen")
    theta = master.addVar(lb=-GRB.INFINITY, name="theta")  # Optimality cut variable

    # Objective: Day-ahead cost + theta
    master.setObjective(
        quicksum(generators[g]["day_ahead_cost"] * da_gen[g] for g in generators) + theta,
        GRB.MINIMIZE
    )

    # Constraints
    master.addConstr(quicksum(da_gen[g] for g in generators) == load, name="load_balance")
    for g in generators:
        master.addConstr(da_gen[g] <= generators[g]["capacity"], name=f"capacity_{g}")

    # Add Benders cuts
    for cut in cuts:
        coeffs, rhs = cut
        master.addConstr(theta >= quicksum(coeffs[g] * da_gen[g] for g in generators) + rhs, name=f"cut_{len(cuts)}")

    master.optimize()

    return master

def solve_subproblems(day_ahead_dispatch):
    """Solves sub-problems for each wind scenario."""
    sub_obj_values = []
    duals = []

    for scenario, wind in enumerate(wind_scenarios):
        sub = Model(f"Subproblem_{scenario}")

        # Variables
        up = sub.addVars(generators.keys(), lb=0, name="up")
        down = sub.addVars(generators.keys(), lb=0, name="down")
        wind_gen = wind * generators["G2"]["capacity"]

        # Objective: Adjustment costs
        sub.setObjective(
            quicksum(
                generators[g]["up_cost"] * up[g] - generators[g]["down_cost"] * down[g]
                for g in generators
            ),
            GRB.MINIMIZE
        )

        # Constraints
        sub.addConstr(
            quicksum(day_ahead_dispatch[g] + up[g] - down[g] for g in generators) + wind_gen == load,
            name="load_balance"
        )
        for g in generators:
            sub.addConstr(up[g] <= generators[g]["up_adj"], name=f"up_limit_{g}")
            sub.addConstr(down[g] <= generators[g]["down_adj"], name=f"down_limit_{g}")
            sub.addConstr(day_ahead_dispatch[g] + up[g] - down[g] <= generators[g]["capacity"], name=f"capacity_{g}")

        sub.optimize()

        if sub.status == GRB.OPTIMAL:
            sub_obj_values.append(probabilities[scenario] * sub.ObjVal)

            dual = [constr.Pi for constr in sub.getConstrs() if constr.constrName == "load_balance"]
            duals.append((dual, sub.ObjVal))

    return sum(sub_obj_values), duals

def benders_algorithm():
    """Implements the Benders decomposition algorithm."""
    cuts = []
    convergence = False
    iteration = 0

    # Initial day-ahead dispatch
    day_ahead_dispatch = {g: load / len(generators) for g in generators}  # Evenly split load

    while not convergence:
        iteration += 1
        print(f"Iteration {iteration}")

        # Solve Master Problem
        master = solve_master(day_ahead_dispatch, cuts)
        day_ahead_dispatch = {g: master.getVarByName(f"day_ahead_gen[{g}]").X for g in generators}
        theta = master.getVarByName("theta").X

        # Solve Sub-problems
        sub_obj, duals = solve_subproblems(day_ahead_dispatch)

        # Convergence check
        if theta >= sub_obj - 1e-4:
            convergence = True
        else:
            for dual, rhs in duals:
                coeffs = {g: dual[g] for g in generators}
                cuts.append((coeffs, rhs))

    print("Benders Decomposition converged.")
    return day_ahead_dispatch

# Run Benders algorithm
optimal_dispatch = benders_algorithm()
print("Optimal Day-Ahead Dispatch:", optimal_dispatch)
