### Sherpa Phase2 models
In this repo, we have created models for phase2. 
We are using mix data. I.e., we are using String level data, weather data and connetor data as well. Now data from the connectors can be available some times and sometimes not. For example, if 10 connectors are there in the string, and we have 5 connector's data available. Similarly, the number of connectors whose data is available can vary from 0-10, in this case. Based on this scenario, we have two different models.:

 **1. Lobby of models:** Based on the available number of connectors, whose data is available, the input size will change. For different input sizes, we have different models, one for each size. 
 
 **2. Generalized model:** We created a model for max number of connectors present in the string, and fixed the input size. Then when we got the data from less number of connetors, we padded that with Substitute values. 

 The repo also contains a python file for a streamlit dashboard to display the measurements of the Exoskeleton deployed at FHB @ Burgdorf, But this works at the staubli end only. As we were not able to generate the system token to get the data. 
