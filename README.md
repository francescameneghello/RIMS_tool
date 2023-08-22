# Runtime Integration of Machine Learning and Simulation for Business Processes (RIMS)

Recent research in Computer Science has investigated the use of Deep Learning (DL) techniques to complement outcomes or decisions within a Discrete event simulation (DES) model. The main idea of this combination is to maintain a white box simulation model but to complement it with information provided by DL models. Indeed, these models are extremely powerful in learning the true relationship between the covariates and the distribution of the output variable, thus avoiding unrealistic or oversimplifying assumptions that are often made when building or discovering simulation models from data. 
State of the art techniques in BPM combine Deep Learning and Discrete event simulation in a post-integration fashion: first an entire simulation is performed, and then a DL model is used to add waiting times and processing times to the events produced by the simulation model. 
In this paper, we aim at taking a step further by introducing \rims (Runtime Integration of Machine Learning and Simulation). Instead of complementing the outcome of a complete simulation with the results of predictions ``a posteriori'', \rims provides a tight integration of the predictions of the DL model \textbf{at runtime} during the simulation. This runtime-integration enables us to fully exploit the specific predictions thus enhancing the performance of the overall system both w.r.t. the single techniques (Business Process Simulation and DL) separately and the post-integration approach. The runtime-integration enables us also to incorporate the queue as an intercase feature in the DL model, thus further improving the performance in process scenarios where the queue plays an important role.

<img src="../old_html_version/rims_schema.png" alt="Alt Text" width="780">

## Installation guide

### Prerequisites
To execute this code, simply install the following main packages:: 

* simpy
* pm4py
* tensorflow
* keras
* pickle
* aggiunti per esempio "statsmodels"

## Getting Started

Once installed all the packages, you can execute the tool from a terminal specifying the following parameters:

* `-p`: specify the path of the Petri net model to be simulated, in *pnml* format
* `-s`: specify the path to the simulation parameter file, in *json* format
* `-t`: specify the total number of traces per single simulation
* `-i`: specify the total number of simulation to generate
* `-o`: specify the path where to save the output files


## Authors

Francesca Meneghello, Chiara Di Francescomarino, Chiara Ghidini
