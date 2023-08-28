
# Example of Arrivals Time and Calendars

For this example we used the log that we can find in the folder *example_arrivals/BPIChallenge2012A.xes*. This event log pertains to a loan application process of a Dutch financial institute. The data contains all applications filed trough an online system in 2016 and their subsequent events until February 1st 2017, 15:11.
The company providing the data and the process under consideration is the same as doi:10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f.

The petrinet found by the inductive miner is the following:

<img src="../example/example_arrivals/petri_net.png" alt="Alt Text" width="780">

In this example we want to show different ways to generate the arrivals times of tokens in the simulation.
As exaplained in the **link inter_trigger_timer class** we can define the arrivals with 3 methods:

* Distribution function: specify in the json file the distribution with the right parameters in seconds, see the [numpy_distribution](https://numpy.org/doc/stable/reference/random/generator.html).
```json
    "interTriggerTimer": {
        "type": "distribution",
        "name": "exponential",
        "parameters": {
            "scale": 20
        }
    }
```

In addition, it is possible to add a schedule for token arrival times, i.e. when a new instance of the process can start. 
For example, we establish that a new trace of this process can start only from Monday to Friday, from 8 a.m. to 3 p.m.

```json
    "interTriggerTimer": {
        "type": "distribution",
        "name": "exponential",
        "parameters": {
            "scale": 20
        },
        "calendar": {
            "days": [1, 2, 3, 4, 5],
            "hour_min": 8,
            "hour_max": 15
        }
    }
```

To set a fixed time interval between arrivals, simply define a uniform distribution with the min and max parameters of the same value.
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

Finally, we defined the two calendars for Role 1 and Role 2 with the following code.
Role 1 resources, Sara and Mike, work Monday through Friday, 8 a.m. to 4 p.m.

```json
   "Role 1": {
        "resources": ["Sara", "Mike"],
        "calendar": {
            "days": [1, 2, 3, 4, 5],
            "hour_min": 8,
            "hour_max": 16
        }
   } 
```

While Role 2 resources, Ellen and Sue, work Monday through Saturday, 8 a.m. to 7 p.m. 

```json
   "Role 2": {
        "resources": ["Ellen", "Sue"],
        "calendar": {
            "days": [1, 2, 3, 4, 5, 6],
            "hour_min": 8,
            "hour_max": 19
        }
   }
```

To run the example use the following commands:

* to run the example with a exponential distribution
```shell
   python main.py -p ../example/example_arrivals/bpi2012.pnml -s ../example/example_arrivals/input_arrivals_example_distribution.json -t 10 -i 1 -o example_arrivals
```

* to run the example with a time series model
```shell
   python main.py -p ../example/example_arrivals/bpi2012.pnml -s ../example/example_arrivals/input_arrivals_example_timeseries.json -t 10 -i 1 -o example_arrivals
```