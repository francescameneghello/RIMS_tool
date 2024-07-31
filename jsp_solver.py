from job_shop_lib import JobShopInstance, Operation
from job_shop_lib.benchmarking import load_benchmark_instance
import matplotlib.pyplot as plt
from job_shop_lib.cp_sat.ortools_solver import ORToolsSolver
from job_shop_lib.visualization import plot_gantt_chart

'''job_1 = [Operation(machines=0, duration=1), Operation(1, 1), Operation(2, 7)]
job_2 = [Operation(1, 5), Operation(2, 1), Operation(0, 1)]
job_3 = [Operation(2, 1), Operation(0, 3), Operation(1, 2)]

jobs = [job_1, job_2, job_3]

instance = JobShopInstance(
    jobs,
    name="Example",
    # Any extra parameters are stored inside the
    # metadata attribute as a dictionary:
    lower_bound=7,
)'''

ft06 = load_benchmark_instance("abz5")

print(ft06.metadata)


solver = ORToolsSolver(max_time_in_seconds=1)
ft06_schedule = solver(ft06)
print(ft06_schedule.schedule)
print(f"Is complete?: {ft06_schedule.is_complete()}")
print(f"Meta data: {ft06_schedule.metadata}")
print(f"Makespan: {ft06_schedule.makespan()}")

fig, ax = plot_gantt_chart(ft06_schedule)
plt.show()