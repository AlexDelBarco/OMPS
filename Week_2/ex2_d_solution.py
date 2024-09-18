import gurobipy as gp
from gurobipy import GRB

# Set values of input parameters
VARIABLES = ['µ1', 'µ2', 'µ3', 'lambda']
objective_coeff = {'µ1': 150, 'µ2': 150, 'µ3': 150, 'lambda': 200}
constraints_coeff = {'µ1': [1, 0, 0], 'µ2': [0, 1, 0], 'µ3': [0, 0, 1], 'lambda': [1, 1, 1]}
constraints_rhs = [70, 0, 150]
constraints_sense = [GRB.LESS_EQUAL, GRB.LESS_EQUAL, GRB.LESS_EQUAL]
lower_bounds={'µ1': -GRB.INFINITY, 'µ2': -GRB.INFINITY, 'µ3': -GRB.INFINITY, 'lambda': -GRB.INFINITY}
upper_bounds={'µ1': 0, 'µ2': 0, 'µ3': 0, 'lambda': GRB.INFINITY}

# Create the Gurobi model
model = gp.Model("Economic dispatch dual")

# Add variables to the Gurobi model
variables = {v: model.addVar(lb=lower_bounds[v], ub=upper_bounds[v], name=v) for v in VARIABLES}

# Set objective function and optimization direction of the Gurobi model
objective = gp.quicksum(objective_coeff[v] * variables[v] for v in VARIABLES)
model.setObjective(objective, GRB.MAXIMIZE)

# Add constraints to the Gurobi model
constraints = [
    (
        model.addLConstr(
                gp.quicksum(constraints_coeff[v][i] * variables[v] for v in VARIABLES),
                constraints_sense[i],
                constraints_rhs[i]
        )
    ) for i in range(len(constraints_rhs))
]

# Optimize the Gurobi model
model.optimize()

# Check if the optimization was successful and print solutions
if model.status == GRB.OPTIMAL:
    print()
    print('-------------------   RESULTS  -------------------')
    optimal_variables = {v: variables[v].x for v in VARIABLES} # Save optimal values of decision variables
    optimal_objective = model.objVal # Save optimal value of objective function
    print("Optimal energy production cost:", optimal_objective)
    for v in VARIABLES:
        print('Optimal {0}:'.format(v), optimal_variables[v])
    print('Optimal dual variables (of the dual problem, i.e., primal variables):')
    print([constr.Pi for constr in constraints])
else:
    print("Optimization was not successful")
