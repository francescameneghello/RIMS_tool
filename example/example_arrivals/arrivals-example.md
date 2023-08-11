
# Example of Decision Mining of petrinet

For this example we used the log that we can find in the folder **example_arrivals/BPIChallenge2012A.xes**. This event log pertains to a loan application process of a Dutch financial institute. The data contains all applications filed trough an online system in 2016 and their subsequent events until February 1st 2017, 15:11.
The company providing the data and the process under consideration is the same as doi:10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f.

The petrinet found by the inductive miner is the following:

<img src="example/example_arrivals/petri_net.png" alt="Alt Text" width="300" height="200">

In this example we want to show different ways to generate the arrivals times of tokens in the simulation.
As exaplained in the <link inter_trigger_timer class> we can define the arrivals with 3 methods:

* Distribution function: specify in the json file the distribution with the right parameters in seconds, see the numpy_distribution distribution, (DISTRIBUTION)
```json
    "interTriggerTimer": {
        "type": "distribution",
        "name": "exponential",
        "parameters": {
            "scale": 20
        }
    }
```
To enter a fixed time interval between arrivals, simply define a uniform distribution with the min and max parameters of the same value.
As in the following example where we set 5 minutes (i.e. 300 seconds) between each token.
```json
    "interTriggerTimer": {
        "type": "distribution",
        "name": "uniform",
        "parameters": {
            "low": 300,
            "high": 300
        }
    }
```
* Custom method: it is possible to define a dedicated method to define the next arrival (CUSTOM).
```json
    "interTriggerTimer": {
        "type": "custom"
    }
```
In the following example we define a simple time series model from the python library
([statsmodels](https://www.statsmodels.org/dev/examples/notebooks/generated/autoregressions.html#)).
The AutoReg model is trained on the real log and then we used it to predict the next token arrival in
the process.

To run the example use the following commands:

* to run the example with a exponential distribution
```shell
   python main.py -p example/example_arrivals/bpi2012.pnml -s example/example_arrivals/input_arrivals_example_distribution.json -t 10 -i 1 -o example_arrivals
```

* to run the example with a time series model
```shell
   python main.py -p example/example_arrivals/bpi2012.pnml -s example/example_arrivals/input_arrivals_example_timeseries.json -t 10 -i 1 -o example_arrivals
```