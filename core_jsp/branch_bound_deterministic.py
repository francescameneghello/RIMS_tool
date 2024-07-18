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
        print('\nSchedule by Job')
        print(schedule.sort_values(by=['Job', 'Start']).set_index(['Job', 'Machine']))
        self.visualize(results)
        return results, schedule['Finish'].max()

    def jobshop(self, Q):
        return self.jobshop_solve(Q)

    def visualize(self, results):
        schedule = pd.DataFrame(results)
        JOBS = sorted(list(schedule['Job'].unique()))
        MACHINES = sorted(list(schedule['Machine'].unique()))
        makespan = schedule['Finish'].max()

        bar_style = {'alpha': 1.0, 'lw': 25, 'solid_capstyle': 'butt'}
        text_style = {'color': 'white', 'weight': 'bold', 'ha': 'center', 'va': 'center'}
        colors = mpl.cm.Dark2.colors

        schedule.sort_values(by=['Job', 'Start'])
        schedule.set_index(['Job', 'Machine'], inplace=True)

        fig, ax = plt.subplots(2, 1, figsize=(12, 5 + (len(JOBS) + len(MACHINES)) / 4))

        for jdx, j in enumerate(JOBS, 1):
            for mdx, m in enumerate(MACHINES, 1):
                if (j, m) in schedule.index:
                    xs = schedule.loc[(j, m), 'Start']
                    xf = schedule.loc[(j, m), 'Finish']
                    ax[0].plot([xs, xf], [jdx] * 2, c=colors[mdx % 7], **bar_style)
                    ax[0].text((xs + xf) / 2, jdx, m, **text_style)
                    ax[1].plot([xs, xf], [mdx] * 2, c=colors[jdx % 7], **bar_style)
                    ax[1].text((xs + xf) / 2, mdx, j, **text_style)

        ax[0].set_title('Job Schedule')
        ax[0].set_ylabel('Job')
        ax[1].set_title('Machine Schedule')
        ax[1].set_ylabel('Machine')

        for idx, s in enumerate([JOBS, MACHINES]):
            ax[idx].set_ylim(0.5, len(s) + 0.5)
            ax[idx].set_yticks(range(1, 1 + len(s)))
            ax[idx].set_yticklabels(s)
            ax[idx].text(makespan, ax[idx].get_ylim()[0] - 0.2, "{0:0.1f}".format(makespan), ha='center', va='top')
            ax[idx].plot([makespan] * 2, ax[idx].get_ylim(), 'r--')
            ax[idx].set_xlabel('Time')
            ax[idx].grid(True)
        fig.tight_layout()
        plt.show()