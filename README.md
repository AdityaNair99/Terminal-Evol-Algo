# Evolutionary Algorithm and Dynamic Scripting

This is an attempt to use the scripting described in a paper titled ["Automatically Generating Game Tactics through Evolutionary Learning"] (https://www.aaai.org/ojs/index.php/aimagazine/article/view/1894) to create an AI for the C1 Terminal Game.

Process is as follows:
1. Randomly generate n chromosomes with fitness over threshold, each of which is composed of n / _cohesion_ genes. A _gene_ is made of _cohesion_ turns from one of the tactics in **tactics.json**
2. Use size-3 tournament selection to pick two parent chromosomes and generate a child chromosome with higher fitness
3. Repeat until best chromosome is found, and write as a tactic to **config.json**

Highest elo - 1374

The **controller.py** file can be run to find a tactic with a fitness higher than a threshold value, which is written to the **config.json** file in the algo directory.

Current Limitations:
- Tactics used are 40% terminal bosses and 60% high elo copies, which produces mediocre results
- Self destruct is hard to detect/counter. Majorly penalizing self destructs seems to help a little 
