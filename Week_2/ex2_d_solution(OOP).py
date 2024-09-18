'''
Here, we reuse the OptimizationProblem class from the Gurobi Tutorial. 
Note that the InputData and OptimizationProblem classes have been modified 
to allow inputting upper and lower bounds  
'''

import gurobipy as gp
from gurobipy import GRB


class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass


class InputData:
    def __init__(
        self,
        VARIABLES: list,
        objective_coeff: dict[str, int],    # Coefficients in objective function
        constraints_coeff: dict[str, int],  # Linear coefficients of constraints
        constraints_rhs: dict[str, int],    # Right hand side coefficients of constraints
        constraints_sense: dict[str, int],  # Direction of constraints
        lower_bounds: dict[str, int],       # Lower bounds for variables 
        upper_bounds: dict[str, int],       # Upper bounds for variables
    ):
        self.VARIABLES = VARIABLES
        self.objective_coeff = objective_coeff
        self.constraints_coeff = constraints_coeff
        self.constraints_rhs = constraints_rhs
        self.constraints_sense = constraints_sense
        self.lower_bounds = lower_bounds
        self.upper_bounds = upper_bounds


class OptimizationProblem():

    def __init__(self, input_data: InputData): # initialize class
        self.data = input_data # define data attributes
        self.results = Expando() # define results attributes
        self._build_model() # build gurobi model
    
    def _build_variables(self):
        self.variables = {
            v: self.model.addVar(
                lb=self.data.lower_bounds[v], 
                ub=self.data.upper_bounds[v], 
                name=f'Total {v}'.format(v),
            ) for v in self.data.VARIABLES
        }
    
    def _build_constraints(self):
        self.constraints = [
            self.model.addConstr(
                gp.quicksum(self.data.constraints_coeff[v][i] * self.variables[v] for v in self.data.VARIABLES),
                self.data.constraints_sense[i],
                self.data.constraints_rhs[i],
            ) for i in range(len(self.data.constraints_rhs))
        ]

    def _build_objective_function(self):
        objective = gp.quicksum(self.data.objective_coeff[v] * self.variables[v] for v in self.data.VARIABLES)
        self.model.setObjective(objective, GRB.MAXIMIZE) 

    def _build_model(self):
        self.model = gp.Model(name='Economic dispatch dual')
        self._build_variables()
        self._build_objective_function()
        self._build_constraints()
        self.model.update()
    
    def _save_results(self):
        self.results.objective_value = self.model.ObjVal
        self.results.variables = {v: self.variables[v].X for v in self.data.VARIABLES}
        self.results.duals = [self.constraints[i].Pi for i in range(len(self.constraints))]

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            print(f"Optimization of {self.model.ModelName} was not successful")
    
    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Optimal objective value:")
        print(self.results.objective_value)
        print("Optimal variable values:")
        print(self.results.variables)
        print("Optimal dual values:")
        print(self.results.duals)


if __name__ == '__main__':
    input_data = InputData(
        VARIABLES = ['µ1', 'µ2', 'µ3', 'lambda'],
        objective_coeff = {'µ1': 150, 'µ2': 150, 'µ3': 150, 'lambda': 200},
        constraints_coeff = {'µ1': [1, 0, 0], 'µ2': [0, 1, 0], 'µ3': [0, 0, 1], 'lambda': [1, 1, 1]}, # 3 constraints, 4 variables 
        constraints_rhs = [70, 0, 150],
        constraints_sense = [GRB.LESS_EQUAL, GRB.LESS_EQUAL, GRB.LESS_EQUAL],
        lower_bounds={'µ1': -GRB.INFINITY, 'µ2': -GRB.INFINITY, 'µ3': -GRB.INFINITY, 'lambda': -GRB.INFINITY},
        upper_bounds={'µ1': 0, 'µ2': 0, 'µ3': 0, 'lambda': GRB.INFINITY},
    )
    problem = OptimizationProblem(input_data)
    problem.run()
    problem.display_results()
