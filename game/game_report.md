# Game Report
## Game configuration
allocation_function: attractiveness_allocation

map_size: (400, 400)

population: 1000000.0

n_rounds: 10

starting_cash: 70000

profit_per_customer: 0.5

max_stores_per_round: 2

place_stores_time_s: 10

ignore_player_exceptions: True

store_config: {'small': {'capital_cost': 10000.0, 'operating_cost': 1000.0, 'attractiveness': 25.0, 'attractiveness_constant': 1.0}, 'medium': {'capital_cost': 50000.0, 'operating_cost': 2000.0, 'attractiveness': 50.0, 'attractiveness_constant': 1.0}, 'large': {'capital_cost': 100000.0, 'operating_cost': 3000.0, 'attractiveness': 100.0, 'attractiveness_constant': 1.0}}

## Players
- Shawty-0
- MaxDensityPlayer-1
- AllocSamplePlayer-2
- AllocSamplePlayer-3
- RandomPlayer-4
## Final Scores
Shawty-0: 418336.3490470187

MaxDensityPlayer-1: 95638.79746064305

AllocSamplePlayer-2: 497152.1153818591

AllocSamplePlayer-3: 251186.45133428514

RandomPlayer-4: 3362.3330661948785

# Winner!
AllocSamplePlayer-2
