import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd

import shutil
import sys
import os.path

#assert(shutil.which("cbc") or os.path.isfile("cbc"))
from pyomo.environ import *
from pyomo.gdp import *


class BBdeterministic(object):

    def __init__(self, problem):
        self.TASKS = problem

    def jobshop_model(self, Q):
        model = ConcreteModel()

        # tasks is a two dimensional set of (j,m) constructed from the dictionary keys
        model.TASKS = Set(initialize=self.TASKS.keys(), dimen=2)

        # the set of jobs is constructed from a python set
        model.JOBS = Set(initialize=list(set([j for (j, m) in model.TASKS])))

        # set of machines is constructed from a python set
        model.MACHINES = Set(initialize=list(set([m for (j, m) in model.TASKS])))

        # the order of tasks is constructed as a cross-product of tasks and filtering
        model.TASKORDER = Set(initialize=model.TASKS * model.TASKS, dimen=4,
                              filter=lambda model, j, m, k, n: (k, n) == self.TASKS[(j, m)]['prec'])

        # the set of disjunctions is cross-product of jobs, jobs, and machines
        model.DISJUNCTIONS = Set(initialize=model.JOBS * model.JOBS * model.MACHINES, dimen=3,
                                 filter=lambda model, j, k, m: j < k and (j, m) in model.TASKS and (
                                 k, m) in model.TASKS)

        # load duration data into a model parameter for later access
        model.dur = Param(model.TASKS,
                          initialize=lambda model, j, m: (self.TASKS[(j, m)]['mean'] + Q * self.TASKS[(j, m)]['std']))

        # establish an upper bound on makespan
        ub = sum([model.dur[j, m] for (j, m) in model.TASKS])

        # create decision variables
        model.makespan = Var(bounds=(0, ub))
        model.start = Var(model.TASKS, bounds=(0, ub))

        model.objective = Objective(expr=model.makespan, sense=minimize)

        model.finish = Constraint(model.TASKS, rule=lambda model, j, m:
        model.start[j, m] + model.dur[j, m] <= model.makespan)

        model.preceding = Constraint(model.TASKORDER, rule=lambda model, j, m, k, n:
        model.start[k, n] + model.dur[k, n] <= model.start[j, m])

        model.disjunctions = Disjunction(model.DISJUNCTIONS, rule=lambda model, j, k, m:
        [model.start[j, m] + model.dur[j, m] <= model.start[k, m],
         model.start[k, m] + model.dur[k, m] <= model.start[j, m]])

        TransformationFactory('gdp.hull').apply_to(model)
        return model

    def jobshop_solve(self, Q):
        solverpath_folder = '/usr/local/Cellar/cbc/2.10.7_1'
        solvername = 'cbc'
        solverpath_exe = '/usr/local/Cellar/cbc/2.10.7_1/bin/cbc'
        sys.path.append(solverpath_folder)
        solver = SolverFactory(solvername, executable=solverpath_exe)
        # SolverFactory('cbc').solve(model)
        model = self.jobshop_model(Q)
        solver.solve(model)
        results = [{'Job': j,
                    'Machine': m,
                    'Start': model.start[j, m](),
                    'Duration': model.dur[j, m],
                    'Finish': model.start[(j, m)]() + model.dur[j, m]}
                   for j, m in model.TASKS]
        schedule = pd.DataFrame(results)
        return results, schedule['Finish'].max()

    def jobshop(self, Q):
        return self.jobshop_solve(Q)