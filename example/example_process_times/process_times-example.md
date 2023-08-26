
# Example of Decision Mining of petrinet

For this example we used the log that we can find in the folder **example_process_times/synthetic_log.xes**.



The petrinet found by the [Inductive Miner](https://pm4py.fit.fraunhofer.de/documentation#item-3-2) algorithm from pm4py, is the following:

<img src="../example/example_process_mining/synthetic_petrinet.png" alt="Alt Text" width="740">


The goal of this example is to present several ways to set the processing time of each task and the 
waiting time between them.


<img src="../example/example_decision_mining/petri_net_decision.png" alt="Alt Text" width="780">

As exaplained in the **link event trace class, next activity** we can define the 3 methods to define the next activity 
of decision point:

* Random choice: each path has equal probability to be chosen for green points (AUTO).
```json
    "probability": {
        "skip_2": "AUTO",
        "A_ACCEPTED": "AUTO",
        "skip_3": "AUTO",
        "A_FINALIZED": "AUTO"
    }
```
* Defined probability: in the file json it is possible to define for each path a specific probability, in this case for the yellow point. (PROBABILITY as value)
```json
    "probability": {
        "A_PREACCEPTED": 0.20,
        "skip_1": 0.80
    }
```
* Custom method: it is possible to define a dedicate method that given the possible paths it returns the one to
  follow, using whatever techniques the user prefers. In this case for the orange point we trained a 
  simple Random Forest to predict the next activity. (CUSTOM) <br />
```json
   "probability": {
      "A_CANCELLED": "CUSTOM",
      "A_DECLINED": "CUSTOM",
      "tauSplit_5": "CUSTOM"
   }
```

To train the model we used as input the following feature: the presence of A_PREACCEPTED, A_ACCEPTED, A_FINALIZED
activities in the prefix of trace, the requested loan amount, the weekday and hour of the time of arrival in the decision point.

<img src="../example/example_decision_mining/random_forest.png" alt="Alt Text" width="780">

In general, if the user does not define probability parameters in the JSON file, the simulator automatically 
applies the AUTO mode for each decision point.
Otherwise, if the user defines the mode for one or more decision points, the user still has to specify all of them even if they are in AUTO mode.


To run the example use the following commands:

* to run the example with a exponential distribution
```shell
   python main.py -p ../example/example_decision_mining/bpi2012.pnml -s ../example/example_decision_mining/input_decision_mining_example.json -t 10 -i 1 -o example_decision_mining
```
