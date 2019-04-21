import numpy as np
import sim
from sim import Game, BigMoneyPlayer
from itertools import permutations


def get_scores(players):
    game = Game(players)
    game.run()

    return [player.score() for player in game.player_states]


def get_n_scores(players, n):
    return np.array([get_scores(players) for i in range(n)])


def get_num_wins(players, n):
    wins = np.zeros(len(players), dtype=np.int64)

    for i in range(n):
        game = Game(players)
        game.run()
        wins[game.get_winners()] += 1

    return wins


def get_num_wins_balanced(players, n):
    wins = np.zeros(len(players), dtype=np.int64)

    for perm in permutations(list(range(len(players)))):
        perm = np.array(perm)
        for i in range(n):
            game = Game([players[pi] for pi in perm])
            game.run()
            wins[perm[game.get_winners()]] += 1

    return wins
