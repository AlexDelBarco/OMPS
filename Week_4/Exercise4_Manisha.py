# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 20:04:12 2024

@author: manis
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np

task = 'linear'

if task == 'quadratic':
    cost_alpha = {'g1': 0.1, 'g2': 0.4, 'g3': 0.2}
if task == 'linear':
    cost_alpha = {'g1': 0, 'g2': 0, 'g3': 0}
    
#params 
generators = ['g1','g2','g3'] 
loads = ['d1']


cost_beta = {'g1': 70, 'g2': 15, 'g3': 150}
gen_capacity = {'g1': 150, 'g2': 150, 'g3': 150}
load_capacity = {'d1': 200}


model = gp.Model('Excercise4_ED')
#add variables
pg = {g:model.addVar(lb=0, ub=GRB.INFINITY, name='Power Generation in G{0}'.format(g)) for g in generators}

model.update()
print(model.NumVars)

#add objective fn

obj = (gp.quicksum(cost_alpha[g] * pg[g]**2 for g in generators) + 
       gp.quicksum(cost_beta[g] * pg[g] for g in generators)
       )
model.setObjective(obj, GRB.MINIMIZE)

#add constraints
#balance constraint 

balance_constraint = model.addLConstr(
    gp.quicksum(pg[g] for g in generators), 
    GRB.EQUAL, 
    load_capacity['d1'], 
    name = 'Balance equation'
    )

#generator constraints
max_production_constraint = {g:model.addConstr(pg[g], GRB.LESS_EQUAL, gen_capacity[g], name = 'Generator{0} max production limit'.format(g)) for g in generators}

#min_production_constraint
min_production_constraint = {g:model.addConstr(-pg[g], GRB.LESS_EQUAL, 0, name = 'Generator{0} min production limit'.format(g)) for g in generators}

model.optimize()

# List all variables and constraints of OPF problem in a vector
variables = model.getVars()
constraints = model.getConstrs()

if model.status == GRB.OPTIMAL:
    print()
    print("-------------------   RESULTS  -------------------")
    optimal_objective = model.ObjVal # save objective value of primal optimization problem at optimality (z^*)
    optimal_sensitivities = [constraints[c].Pi for c in range(len(constraints))] #save value of dual variables associated with each primal constraint at optimality
    print("Optimal production cost of {0}:".format(model.ModelName), optimal_objective)
    print("Optimal dispatches of generators:")
    for i in generators:
        print(f"Generator {i}: {pg[i].x:.2f}")
      
    print(f'Optimal duals of balance equations: {balance_constraint.Pi:.3f}')
    print(f'Slack: {balance_constraint.Slack:.3f}')
    print("Optimal duals of max production constraints:")
    for i in generators:
        print(f"Dual U_{i} : {max_production_constraint[i].Pi:.3f}")
        print(f"Slack U_{i} : {max_production_constraint[i].Slack:.3f}")
    print("Optimal duals of min production constraints:")
    for i in generators:
        print(f"Dual u_{i} : {min_production_constraint[i].Pi:.3f}")
        print(f"Slack u_{i} : {min_production_constraint[i].Slack:.3f}")

        
else:
    raise RuntimeError("optimization of {0} was not successful".format(model.ModelName))
 


"""
-------------------   RESULTS Quadratic -------------------
Optimal production cost of Excercise4_ED: 13487.500000000167
Optimal dispatches of generators:
Generator g1: 105.00
Generator g2: 95.00
Generator g3: 0.00
Optimal duals of balance equations: 91.000
Slack: 0.000
Optimal duals of max production constraints:
Dual U_g1 : -0.000
Slack U_g1 : 45.000
Dual U_g2 : -0.000
Slack U_g2 : 55.000
Dual U_g3 : -0.000
Slack U_g3 : 150.000
Optimal duals of min production constraints:
Dual u_g1 : -0.000
Slack u_g1 : 105.000
Dual u_g2 : -0.000
Slack u_g2 : 95.000
Dual u_g3 : -0.000
Slack u_g3 : 0.000

c) The quadratic optimization problem is convex. 

Are the dual varibles negative  U_g and u_g ?

Verifying the KKT conditions - 
1) Primal feasibility
    Generator g1: 105.00 < Pg1
    Generator g2: 95.00 < Pg2
    Generator g3: 0.00 < Pg3
    
    pg1 + pg2 + pg3 = Ld

2) Dual feasibility
    Lagrange multiplier U >= 0
    
    lamda = 91.000 > 0
    Ug >= 0
    ug >= 0
    
3) Complementary Slackness 
    U * g(x) = 0
    
    For inequality contraint of max_generation_limits
    1) G1: (pg1 - Pg1) = (105 - 150) < 0  and U_g1 = 0
    2) G2: (pg2 - Pg2) < 0 and U_g2 = 0
    3) G3: (pg3 - Pg3) < 0 and U_g3 = 0

    KKT conditions are satisfied - 
    
Note: -
Slack (LHS - RHS) is positive and dual is 0 - complementary slackness satisfied
or
Slack (LHS - RHS) is 0 and dual is positive - complementary slackness satisfied
    
"""

"""
-------------------   RESULTS  Linear -------------------
Optimal production cost of Excercise4_ED: 5750.0
Optimal dispatches of generators:
Generator g1: 50.00
Generator g2: 150.00
Generator g3: 0.00
Optimal duals of balance equations: 70.000
Slack: 0.000
Optimal duals of max production constraints:
Dual U_g1 : 0.000
Slack U_g1 : 100.000
Dual U_g2 : -55.000
Slack U_g2 : 0.000
Dual U_g3 : 0.000
Slack U_g3 : 150.000
Optimal duals of min production constraints:
Dual u_g1 : 0.000
Slack u_g1 : 50.000
Dual u_g2 : 0.000
Slack u_g2 : 150.000
Dual u_g3 : 0.000
Slack u_g3 : 0.000

Verifying the KKT conditions - 
1) Primal feasibility
    Generator g1: 50.00 < Pg1
    Generator g2: 150.00 = Pg2
    Generator g3: 0.00 < Pg3
    
    pg1 + pg2 + pg3 = Ld

2) Dual feasibility
    Lagrange multiplier U >= 0
    
    lamda = 70.000 > 0
    U_g2 : -55.000 < 0 -- is this not satisfied ? 
    ug >= 0
    
3) Complementary Slackness 
    U * g(x) = 0
    
    For inequality contraint of max_generation_limits
    1) G1: (pg1 - Pg1) = (50 - 150) < 0  and U_g1 = 0
    2) G2: (pg2 - Pg2) = 0 and U_g2 = -55 -- is the complementary slackness not satisfied here ? 
    3) G3: (pg3 - Pg3) < 0 and U_g3 = 0
    
KKT conditions are not satisfied.
"""

"""
How to differentiate between Lagrangian duality and LP duality in Gurobipy?
"""