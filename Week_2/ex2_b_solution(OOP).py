'''
Here, we introduce a more specific class called EconomicDispatch to solve the economic dispatch problem. 
Note that the InputData class has also been modified to be specific for the economic dispatch problem. 
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
        GENERATORS: list, 
        LOADS: list, 
        generator_cost: dict[str, int],     
        generator_capacity: dict[str, int], 
        load_capacity: dict[str, int]
    ):
        # List of generators 
        self.GENERATORS = GENERATORS
        # List of loads
        self.LOADS = LOADS
        # Generators costs (c^G_i)
        self.generator_cost = generator_cost 
        # Generators capacity (P^G_i)
        self.generator_capacity = generator_capacity 
        # Loads capacity (P^D_i)
        self.load_capacity = load_capacity 


class EconomicDispatch():

    def __init__(self, input_data: InputData): # initialize class
        self.data = input_data # define data attributes
        self.variables = Expando() # define variable attributes
        self.constraints = Expando() # define constraints attributes
        self.results = Expando() # define results attributes
        self._build_model() # build gurobi model
    
    def _build_variables(self):
        # build generator production variables
        self.variables.generator_production = {
            g: self.model.addVar(
                lb=0, name='Electricity production of generator {0}'.format(g)
            ) for g in self.data.GENERATORS
        }
    
    def _build_constraints(self):
        # build capacity constraints 
        self.constraints.capacity_constraints = {
            g: self.model.addLConstr(
                self.variables.generator_production[g], 
                GRB.LESS_EQUAL,
                self.data.generator_capacity[g],
            ) for g in self.data.GENERATORS
        }
        # build balance constraint
        self.constraints.balance_constraint = (
            self.model.addLConstr(
                gp.quicksum(self.variables.generator_production[g] for g in self.data.GENERATORS),
                GRB.EQUAL,
                gp.quicksum(self.data.load_capacity[d] for d in self.data.LOADS),
                name='Balance constraint',
            )
        )

    def _build_objective_function(self):
        objective = gp.quicksum(
            self.data.generator_cost[g] * self.variables.generator_production[g] for g in self.data.GENERATORS
        )
        self.model.setObjective(objective, GRB.MINIMIZE)

    def _build_model(self):
        self.model = gp.Model(name='Economic dispatch')
        self._build_variables()
        self._build_objective_function()
        self._build_constraints()
        self.model.update()
    
    def _save_results(self):
        # save objective value
        self.results.objective_value = self.model.ObjVal
        # save generator dispatch values
        self.results.generator_production = {
            g: self.variables.generator_production[g].x for g in self.data.GENERATORS
        }
        # save price (i.e., dual variable of balance constraint)
        self.results.price = self.constraints.balance_constraint.Pi
        # save generator capacity sensitivities (i.e., dual variables of capacity constraints)
        self.results.capacity_sensitivities = {
            g: self.constraints.capacity_constraints[g].Pi for g in self.data.GENERATORS
        }

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            print(f"optimization of {model.ModelName} was not successful")
    
    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Optimal energy production cost:")
        print(self.results.objective_value)
        print("Optimal generator dispatches:")
        print(self.results.generator_production)
        print("Price at optimality:")
        print(self.results.price)
        print("Capacity sensitivities")
        print(self.results.capacity_sensitivities)


if __name__ == '__main__':
    input_data = InputData(
        GENERATORS = ['G1', 'G2', 'G3'],
        LOADS = ['L1'],
        generator_cost = {'G1': 70, 'G2': 0, 'G3': 150}, # Generators costs (c^G_i)
        generator_capacity = {'G1': 150, 'G2': 150, 'G3': 150}, # Generators capacity (P^G_i)
        load_capacity = {'L1': 200}, # Loads capacity (P^D_i)
    )
    ec_model = EconomicDispatch(input_data)
    ec_model.run()
    ec_model.display_results()
