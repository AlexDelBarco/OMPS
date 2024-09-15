#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 21:19:15 2024

@author: lesiamitridati
"""

# Import packages
import gurobipy as gb
from gurobipy import GRB


#%%


# Create a Gurobi model       
model_primal = gb.Model("Bestas primal problem")


# Set time limit
model_primal.Params.TimeLimit = 100 


# Add variables to the Gurobi model
xE = model_primal.addVar(lb=0)
xH = model_primal.addVar(lb=0)

# Set objective function and optimization direction of the Gurobi model
      
model_primal.setObjective(xE*10+xH*15, gb.GRB.MAXIMIZE)


# Add constraints to the Gurobi model
constraint1_primal = model_primal.addConstr(
        xE,
        gb.GRB.LESS_EQUAL,
        100)

constraint2_primal = model_primal.addConstr(
         xH,
         gb.GRB.LESS_EQUAL,
         100)

constraint3_primal = model_primal.addConstr(
         xE+xH/0.8,
         gb.GRB.LESS_EQUAL,
         200)

model_primal.optimize()


#%%

# Create a Gurobi model       
model_dual = gb.Model("Bestas dual problem")


# Set time limit
model_dual.Params.TimeLimit = 100 


# Add variables to the Gurobi model
yE_dual = model_dual.addVar(lb=0)
yH_dual = model_dual.addVar(lb=0)
yW_dual = model_dual.addVar(lb=0)

# Set objective function and optimization direction of the Gurobi model
      
model_dual.setObjective(yE_dual*100+yH_dual*100+yW_dual*200, gb.GRB.MINIMIZE)


# Add constraints to the Gurobi model
constraint1_dual = model_dual.addConstr(
        yE_dual+yW_dual,
        gb.GRB.GREATER_EQUAL,
        10)

constraint2_dual = model_dual.addConstr(
         yH_dual+yW_dual/0.8,
         gb.GRB.GREATER_EQUAL,
         15)

model_dual.optimize()


#%% get dual variables 


yH_dual.x

constraint2_primal.pi

#%%

# Create a Gurobi model       
model_baersk = gb.Model("Baersk primal problem")


# Set time limit
model_baersk.Params.TimeLimit = 100 


# Add variables to the Gurobi model
yE_baersk = model_baersk.addVar(lb=0)
yH_baersk = model_baersk.addVar(lb=0)
yW_baersk = model_baersk.addVar(lb=0)

# Set objective function and optimization direction of the Gurobi model
      
model_baersk.setObjective(yE_baersk*100+yH_baersk*100+yW_baersk*(200-100-100/0.8), gb.GRB.MINIMIZE)


# Add constraints to the Gurobi model
constraint1_baersk = model_baersk.addConstr(
        yE_baersk,
        gb.GRB.GREATER_EQUAL,
        10)

constraint2_baersk = model_baersk.addConstr(
         yH_baersk,
         gb.GRB.GREATER_EQUAL,
         15)

constraint3_baersk = model_baersk.addConstr(
         yW_baersk,
         gb.GRB.LESS_EQUAL,
         yE_baersk)

constraint4_baersk = model_baersk.addConstr(
         yW_baersk,
         gb.GRB.LESS_EQUAL,
         yH_baersk*0.8)


model_baersk.optimize()