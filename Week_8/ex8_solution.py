import gurobipy as gp
from gurobipy import GRB
import numpy as np


class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass


class InputData:
    
    def __init__(
        self, 
        SCENARIOS: list,
        GENERATORS: list,
        load_capacity: float,
        generator_DA_cost: dict[str, float],
        generator_up_cost: dict[str, float],
        generator_down_cost: dict[str, float],
        generator_capacity: dict[str, float],
        generator_up_capacity: dict[str, float],
        generator_down_capacity: dict[str, float],
        wind_error: dict[str, float],
        wind_error_oos: dict[str, float],
        wind_mean: float,
    ):
        self.SCENARIOS = SCENARIOS
        self.pi = {SCENARIOS[i]: 1/len(SCENARIOS) for i in range(len(SCENARIOS))}
        self.GENERATORS = GENERATORS
        self.load_capacity = load_capacity
        self.generator_DA_cost = generator_DA_cost
        self.generator_up_cost = generator_up_cost
        self.generator_down_cost = generator_down_cost
        self.generator_capacity = generator_capacity
        self.generator_up_capacity = generator_up_capacity
        self.generator_down_capacity = generator_down_capacity
        self.wind_error = wind_error
        self.wind_error_oos = wind_error_oos
        self.wind_mean = wind_mean


class StochasticEconomicDispatch():

    def __init__(self, input_data: InputData, epsilon: float = 0.0):
        self.data = input_data
        self.epsilon = epsilon
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.model = self._build_model()

    def _build_variables(self, model: gp.Model):
        self.variables.generator_DA_production = {
            g: model.addVar(
                lb=0, ub=self.data.generator_capacity[g], name='DA dispatch'
            ) for g in self.data.GENERATORS
        }
        self.variables.up_regulation = {
            (g,k): model.addVar(
                lb=0, ub=self.data.generator_up_capacity[g], name='Up-regulation in BM'
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        }
        self.variables.down_regulation = {
            (g,k): model.addVar(
                lb=0, ub=self.data.generator_down_capacity[g], name='Down-regulation in BM'
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        }
        # add binary variables for chance constraints
        self.big_M = 10000
        self.variables.binary_RT_balance = {
            k: model.addVar(
                vtype=GRB.INTEGER, name='Binary var for real-time balance constraint'
            ) for k in self.data.SCENARIOS
        }
        self.variables.binary_max_production = {
            k: model.addVar(
                vtype=GRB.INTEGER, name='Binary var for max production constraint'
            ) for k in self.data.SCENARIOS
        }
        self.variables.binary_max_ramp = {
            k: model.addVar(
                vtype=GRB.INTEGER, name='Binary var for max ramp constraint'
            ) for k in self.data.SCENARIOS
        }
        
        return model

    def _build_constraints(self, model: gp.Model, oos: bool = False):
        self.constraints.DA_balance = model.addConstr(
            gp.quicksum(
                self.variables.generator_DA_production[g]
                for g in self.data.GENERATORS
            ),
            GRB.EQUAL,
            self.data.load_capacity,
            name='Day-ahead balance equation',
        )
        self.constraints.RT_balance_lower = {
            k: model.addConstr(
                gp.quicksum(
                    self.variables.up_regulation[(g,k)] - self.variables.down_regulation[(g,k)]
                    for g in self.data.GENERATORS
                ),
                GRB.GREATER_EQUAL,
                (-(1 - self.variables.binary_RT_balance[k]) * self.big_M),
                name='Real-time balance equation',
            ) for k in self.data.SCENARIOS
        }
        self.constraints.RT_balance_upper = {
            k: model.addConstr(
                gp.quicksum(
                    self.variables.up_regulation[(g,k)] - self.variables.down_regulation[(g,k)]
                    for g in self.data.GENERATORS
                ),
                GRB.LESS_EQUAL,
                ((1 - self.variables.binary_RT_balance[k]) * self.big_M),
                name='Real-time balance equation',
            ) for k in self.data.SCENARIOS
        }
        self.constraints.min_production_constraints = {
            (g,k): model.addLConstr(
                (- (1 - self.variables.binary_max_production[k]) * self.big_M),
                GRB.LESS_EQUAL,
                (
                    self.variables.generator_DA_production[g]
                    + self.variables.up_regulation[(g,k)] 
                    - self.variables.down_regulation[(g,k)]
                ),
                name='Min production constraint',
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        }
        self.constraints.max_production_constraints = {
            (g,k): model.addLConstr(
                (
                    self.variables.generator_DA_production[g]
                    + self.variables.up_regulation[(g,k)] 
                    - self.variables.down_regulation[(g,k)]
                    - self.data.generator_capacity[g]
                ),
                GRB.LESS_EQUAL,
                (1 - self.variables.binary_max_production[k]) * self.big_M,
                name='Max production constraint',
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS if g != 'G2'
        }
        self.constraints.max_production_constraints_G2 = {
            k: model.addLConstr(
                (
                    self.variables.generator_DA_production['G2']
                    + self.variables.up_regulation[('G2',k)] 
                    - self.variables.down_regulation[('G2',k)]
                )
                - (
                    self.data.wind_mean 
                    + self.data.generator_capacity['G2']
                    * (self.data.wind_error_oos[k] if oos else self.data.wind_error[k])
                ),
                GRB.LESS_EQUAL,
                ((1 - self.variables.binary_max_production[k]) * self.big_M),
                name='Max production constraint',
            ) for k in self.data.SCENARIOS
        }
        self.constraints.max_ramp_up_constraints = {
            (g,k): model.addLConstr(
                self.variables.up_regulation[(g,k)] - self.data.generator_up_capacity[g],
                GRB.LESS_EQUAL,
                ((1 - self.variables.binary_max_ramp[k]) * self.big_M),
                name='Max up-regulation constraint',
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        }
        self.constraints.max_ramp_down_constraints = {
            (g,k): model.addLConstr(
                self.variables.down_regulation[(g,k)] - self.data.generator_down_capacity[g],
                GRB.LESS_EQUAL,
                ((1 - self.variables.binary_max_ramp[k]) * self.big_M),
                name='Max down-regulation constraint',
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        }
        # Constraints on rate of violation for RT constraints
        self.constraints.binary_RT_balance = model.addLConstr(
            gp.quicksum(
                self.variables.binary_RT_balance[k] for k in self.data.SCENARIOS
            ) / len(self.data.SCENARIOS),
            GRB.GREATER_EQUAL,
            1 - self.epsilon,
            name='Binary RT constraint',
        )
        self.constraints.binary_max_production = model.addLConstr(
            gp.quicksum(
                self.variables.binary_max_production[k] for k in self.data.SCENARIOS
            ) / len(self.data.SCENARIOS),
            GRB.GREATER_EQUAL,
            1 - self.epsilon,
            name='Binary max production constraint',
        )
        self.constraints.binary_max_ramp = model.addLConstr(
            gp.quicksum(
                self.variables.binary_max_ramp[k] for k in self.data.SCENARIOS
            ) / len(self.data.SCENARIOS),
            GRB.GREATER_EQUAL,
            1 - self.epsilon,
            name='Binary max ramp constraint',
        )
        
        return model

    def _build_objective_function(self, model: gp.Model, oos: bool = False):
        # DA costs
        DA_cost = gp.quicksum(
            self.data.generator_DA_cost[g] * self.variables.generator_DA_production[g]
            for g in self.data.GENERATORS
        )
        # Balancing costs
        B_cost = gp.quicksum(
            self.data.pi[k] * (
                self.data.generator_up_cost[g] * self.variables.up_regulation[(g,k)]
                - self.data.generator_down_cost[g] * self.variables.down_regulation[(g,k)]
            ) for k in self.data.SCENARIOS for g in self.data.GENERATORS
        )
        # Penalization of constraint violation 
        if oos:
            penalty = (
                gp.quicksum(
                    self.big_M * (1 - self.variables.binary_RT_balance[k]) for k in self.data.SCENARIOS
                )
                + gp.quicksum(
                    self.big_M * (1 - self.variables.binary_max_production[k]) for k in self.data.SCENARIOS
                )
                + gp.quicksum(
                    self.big_M * (1 - self.variables.binary_max_ramp[k]) for k in self.data.SCENARIOS
                )
            )
        else: 
            penalty = 0
        model.setObjective(DA_cost + B_cost + penalty, GRB.MINIMIZE)

        return model

    def _build_model(self, oos: bool = False):
        model = gp.Model(name='Two-stage stochastic economic dispatch')
        model = self._build_variables(model)
        model = self._build_constraints(model, oos)
        model = self._build_objective_function(model, oos)
        model.update()
        return model

    def _save_results(self):
        self.results.objective_value = self.model.ObjVal
        self.results.generator_DA_production = {
            g: self.variables.generator_DA_production[g].x
            for g in self.data.GENERATORS
        }
        self.results.up_regulation = {
            k: {
                g: self.variables.up_regulation[(g,k)].x 
                for g in self.data.GENERATORS
            } for k in self.data.SCENARIOS
        }
        self.results.down_regulation = {
            k: {
                g: self.variables.down_regulation[(g,k)].x
                for g in self.data.GENERATORS
            } for k in self.data.SCENARIOS
        }
        self.results.DA_price = self.fixed_model.getConstrs()[0].Pi
        self.results.B_price = {
            k: 10 * self.fixed_model.getConstrs()[i+1].Pi for i,k in enumerate(self.data.SCENARIOS)
        }
        self.results.DA_profits = {
            g: round((self.results.DA_price - self.data.generator_DA_cost[g]) * self.results.generator_DA_production[g], 2)
            for g in self.data.GENERATORS
        }
        self.results.B_profits = {
            g: {
                k: round(
                    (self.results.B_price[k] - self.data.generator_up_cost[g]) * self.results.up_regulation[k][g] 
                    + (self.data.generator_down_cost[g] - self.results.B_price[k]) * self.results.down_regulation[k][g], 
                    2,
                )
                for k in self.data.SCENARIOS
            } for g in self.data.GENERATORS
        }
        self.results.B_exp_profits = {
            g: round(np.mean(list(self.results.B_profits[g].values()))) 
            for g in self.data.GENERATORS
        }

    def run(self):
        self.model.optimize()
        self.fixed_model = self.model.fixed()
        self.fixed_model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            raise RuntimeError(f'optimization of {self.model.ModelName} was not successful')

    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Expected cost:")
        print(self.results.objective_value)
        print("Optimal DA dispatch:")
        print(self.results.generator_DA_production)
        print("Optimal up-regulation:")
        for k in self.data.SCENARIOS:
            print(f"{k}: {self.results.up_regulation[k]}")
        print("Optimal down-regulation:")
        for k in self.data.SCENARIOS:
            print(f"{k}: {self.results.down_regulation[k]}")
        print("DA profits:")
        print(self.results.DA_profits)
        print("Balancing profits in expectation:")
        print(self.results.B_exp_profits)
        print("Balancing profits in each scenario:")
        for g in self.data.GENERATORS:
            print(f"{g}: {self.results.B_profits[g]}")
        print()
        print("--------------------------------------------------")
    
    def _build_oos_constraints(self, model: gp.Model):
        self.constraints.oos_fixed_DA_constraints = {
            g: self.model.addLConstr(
                self.variables.generator_DA_production[g],
                GRB.EQUAL,
                self.results.generator_DA_production[g],
                name='Out-of-sample fixed DA dispatch constraint',
            ) for g in self.data.GENERATORS
        }
        return model

    def build_out_of_sample(self):
        # epsilon is set to 0 to allow constraint violations instead of having an infeasible model
        # constraint violations are penalized in the objective function 
        self.epsilon = 1
        self.model = self._build_model(oos=True)
        self.model = self._build_oos_constraints(self.model)


if __name__ == '__main__':
    input_data = InputData(
        SCENARIOS=[f'S{i}' for i in range(1,11)],
        GENERATORS=[f'G{i}' for i in range(1,4)],
        load_capacity=200,
        generator_DA_cost={'G1': 75, 'G2': 6, 'G3': 80},
        generator_up_cost={'G1': 77, 'G2': 8, 'G3': 82},
        generator_down_cost={'G1': 74, 'G2': 5, 'G3': 79},
        generator_capacity={'G1': 100, 'G2': 150, 'G3': 50},
        generator_up_capacity={'G1': 10, 'G2': 150, 'G3': 50},
        generator_down_capacity={'G1': 10, 'G2': 150, 'G3': 50},
        wind_error={
            'S1': -0.09,'S2': -0.04, 'S3': -0.10, 'S4': 0.08, 'S5': 0.07, 
            'S6': 0.04, 'S7': 0.06, 'S8': -0.01, 'S9': 0.02, 'S10': 0.07
        },
        wind_error_oos={
            'S1': 0.09,'S2': -0.09, 'S3': 0.12, 'S4': -0.07, 'S5': 0.04, 
            'S6': 0.04, 'S7': -0.15, 'S8': -0.02, 'S9': 0.07, 'S10': -0.01
        },
        wind_mean=110,
    )
    # (b)
    model = StochasticEconomicDispatch(input_data, epsilon=0)
    model.run()
    model.display_results()

    # (c)
    model.build_out_of_sample()
    model.run()
    model.display_results()

    # (e)-(f)
    for epsilon in [0.1, 0.2, 0.3]:
        model = StochasticEconomicDispatch(input_data, epsilon=epsilon)
        model.run()
        model.display_results()

        model.build_out_of_sample()
        model.run()
        model.display_results()
