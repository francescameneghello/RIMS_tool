
# Example of Decision Mining of petrinet

For this example we used the log that we can find in the folder **example_decision_mining/BPIChallenge2012A.xes**. This event log pertains to a loan application process of a Dutch financial institute. The data contains all applications filed trough an online system in 2016 and their subsequent events until February 1st 2017, 15:11.
The company providing the data and the process under consideration is the same as doi:10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f.

The petrinet found by the inductive miner is the following:

<img src="../example/example_decision_mining/petri_net.png" alt="Alt Text" width="300" height="200">

For this example we want to show also how to add the specific case attribute for this
log i.e. the amount of requested loan. Through the function **attribute_function_case(case_id)**
it is easy to add the attribute/s case with the return of dictionary.

```python
    def attribute_function_case(case):
        return {"AMOUNT": random.randint(100, 99999)}
```




In this example, we want to show different ways to choose the next activity from a specific decision point. 
In the following image, the four decision points in the process are outlined and the three ways allowed by the simulator have been applied.

<img src="../example/example_decision_mining/petri_net_decision.png" alt="Alt Text" width="300" height="200">

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
  simple Random Forest to predict the next activity. (CUSTOM)
```json
   "probability": {
      "A_CANCELLED": "CUSTOM",
      "A_DECLINED": "CUSTOM",
      "tauSplit_5": "CUSTOM"
   }
```

To run the example use the following commands:

* to run the example with a exponential distribution
```shell
   python main.py -p example/example_decision_mining/bpi2012.pnml -s example/example_decision_mining/input_decision_mining_example.json -t 10 -i 1 -o example_decision_mining
```
