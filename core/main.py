"""
.. include:: ../README.md
.. include:: ../example/example_arrivals/arrivals-example.md
.. include:: ../example/example_decision_mining/decision_mining-example.md
.. include:: ../example/example_process_times/process_times-example.md
"""


import warnings
from run_simulation import main
import sys

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])