# Dominionator

Simulate just enough of Dominion to test out some strategies.

## Files

### [sim.py](dominionator/sim.py)

Main simulation code; card definitions, game state etc.

### [players.py](dominionator/players.py)

Player strategy implementations.

### [experiment.py](dominionator/experiment.py)

Functions useful for experimenting with players -- run a bunch of simulations
and summarize the results.

## Examples

Run 1000 simulations comparing two strategies (in the two possible orders),
returning the number of wins that each had:

```python
>>> dominionator.experiment.get_num_wins_balanced([ 
...     dominionator.players.BigMoneyPlayerBasic(4),
...     dominionator.players.BigMoneyPlayerWiki(True),
... ], 1000)
array([ 450, 1612])
```
