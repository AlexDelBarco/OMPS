# Import packages
import gurobipy as gp
from gurobipy import GRB

# Set values of input parameters
VARIABLES = ['x^E', 'x^H'] # Variables in (kWh)
objective_coeff = {'x^E': 10, 'x^H': 15} # Coefficients in objective function
constraints_coeff = {'x^E': [1, 0, 1], 'x^H': [0, 1, 1/0.8]} # Linear coefficients of constraints
constraints_rhs = [100, 100, 200] # Right hand side coefficients of constraints
constraints_sense = [GRB.LESS_EQUAL, GRB.LESS_EQUAL, GRB.LESS_EQUAL] # Direction of constraints

# Create the Gurobi model
model = gp.Model("Bestas problem")

# Add variables to the Gurobi model
variables = {v: model.addVar(lb=0, name=v) for v in VARIABLES}

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
else:
        print("Optimization was not successful")
