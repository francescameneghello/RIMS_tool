"""
.. include:: ../README.md
.. include:: ../example/example_arrivals/arrivals-example.md
"""


import warnings
from run_simulation import main
import sys

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main(sys.argv[1:])