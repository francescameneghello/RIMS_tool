
# Example of Decision Mining of petrinet

For this example we used a simple synthetic event log (running-example.xes) can be downloaded from
[pm4py site](https://pm4py.fit.fraunhofer.de/static/assets/examples/running-example.xes).

The petrinet found by the inductive miner is the following:

**insert image**

In particular we used the example of pm4py that used a simple decision tree to define the path of a decision point
([Decision Mining](https://pm4py.fit.fraunhofer.de/documentation#item-7-3)).

In this case we want to predict only the path to follow from the XOR-split(<span style="color:orange">p_10</span>) as we can see from the Figure (i.e performing the ac
tivity **examine casually** or **examine throughly**). While for the other XOR-split we used the random probability **AUTO**(<span style="color:green">p_4</span>) or a 
defined probability (<span style="color:purple">p_4</span>). 
So in the file json the specification is the following:
```json
    "probability": {
        "51e11ae8-b45f-4e63-9a72-761a445207bb": "CUSTOM",
        "df3ccb03-7726-4bc4-a58e-64300079c499": "CUSTOM",
        "21faea29-a88b-490d-b9af-67d1cf80487c": 0.10,
        "skip_5": 0.90,
        "a7a9a946-d877-4f3e-bca4-4ad966edc2e0": "AUTO",
        "c3856dfd-458a-4833-b755-0504af2d3b0f": "AUTO"
    }
```
Pm4py provide a function to automate the discovery of decision trees out of the decision mining technique. The resulted decision tree is the 
following(Figure 3) and we know also the feature names needed to predict the next activity.

classes ['examine casually': 0, 'examine thoroughly': 1]

```python 
from pm4py.algo.decision_mining import algorithm as decision_mining
clf, feature_names, classes = decision_mining.get_decision_tree(log, net, im, fm, decision_point="p_10")
```

```python 
['org:resource_Ellen',
 'org:resource_Mike',
 'org:resource_Sean',
 'org:resource_Sue',
 'Costs_100',
 'Costs_400',
 'Resource_Ellen',
 'Resource_Mike',
 'Resource_Sean',
 'Resource_Sue',
 'Activity_check ticket',
 'Activity_examine casually',
 'Activity_examine thoroughly']
```

**insert image 2**




