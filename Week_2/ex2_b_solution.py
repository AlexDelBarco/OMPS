import gurobipy as gp
from gurobipy import GRB

# Set values of input parameters
GENERATORS = ['G1', 'G2', 'G3']
LOADS = ['L1']
generator_cost = {'G1': 70, 'G2': 0, 'G3': 150}         # Generators costs (c^G_i)
generator_capacity = {'G1': 150, 'G2': 150, 'G3': 150}  # Generators capacity (P^G_i)
load_capacity = {'L1': 200}                             # Loads capacity (P^D_i)

# Create the Gurobi model
model = gp.Model("Economic dispatch")

# Add variables to the Gurobi model
generator_production = {
    g: model.addVar(
        lb=0, name='Electricity production of generator {0}'.format(g)
    ) for g in GENERATORS
}

# Set objective function and optimization direction of the Gurobi model
objective = gp.quicksum(
    generator_cost[g] * generator_production[g] for g in GENERATORS
)
model.setObjective(objective, GRB.MINIMIZE)

# Add constraints to the Gurobi model
# capacity constraints 
capacity_constraints = {
    g: model.addLConstr(
        generator_production[g], 
        GRB.LESS_EQUAL,
        generator_capacity[g],
    ) for g in GENERATORS
}
# balance constraint
balance_constraint = (
    model.addLConstr(
        gp.quicksum(generator_production[g] for g in GENERATORS),
        GRB.EQUAL,
        gp.quicksum(load_capacity[d] for d in LOADS),
        name='Balance constraint',
    )
)

# Optimize the Gurobi model
model.optimize()

# Check if the optimization was successful and print solutions
if model.status == GRB.OPTIMAL:
    print()
    print('-------------------   RESULTS  -------------------')
    optimal_objective = model.objVal 
    print("Optimal energy production cost:", optimal_objective)
    print("Optimal generator dispatches:")
    optimal_generator_production = {
        g: generator_production[g].x for g in GENERATORS
    }
    print(optimal_generator_production)
    print('Price at optimality:')
    print(balance_constraint.Pi)
    print('Capacity sensitivities:')
    capacity_sensitivities = {
            g: capacity_constraints[g].Pi for g in GENERATORS
        }
    print(capacity_sensitivities)
else:
    print("Optimization was not successful")
