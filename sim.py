from attr import attrs, attrib, Factory
from random import shuffle
from collections import OrderedDict, defaultdict
from types import SimpleNamespace


@attrs(frozen=True)
class Card(object):
    name = attrib()
    cost = attrib()

    gold = attrib(default=0)

    victory = attrib(default=0)


_card_types = [
    Card("estate", 2, victory=1),
    Card("duchy", 5, victory=3),
    Card("province", 8, victory=6),
    Card("copper", 0, gold=1),
    Card("silver", 3, gold=2),
    Card("gold", 6, gold=3),
]

card_types = OrderedDict((card.name, card) for card in _card_types)


class Move(object):
    pass


@attrs
class Buy(Move):
    card = attrib()


class Game(object):
    def __init__(self, players):
        self.players = players
        self.player_states = [self.PlayerState() for player in self.players]

        start_cards = [
            ("copper", 60 - 7 * len(players)),
            ("silver", 40),
            ("gold", 30),
            ("estate", 8),
            ("duchy", 8),
            ("province", 8),
        ]
        self.supply = defaultdict(
            lambda: 0, [(card_types[t], n) for t, n in start_cards]
        )

        self.trash = []

    @attrs
    class PlayerState(object):
        deck = attrib(default=Factory(list))
        discard = attrib()
        num_turns = attrib(default=0)

        @discard.default
        def _discard_default(self):
            return [card_types["copper"]] * 7 + [card_types["estate"]] * 3

        def get_cards(self, n):
            """Get n cards from the deck, shuffling if necessary."""
            if len(self.deck) < n:
                shuffle(self.discard)
                self.deck, self.discard = self.deck + self.discard, []

            if len(self.deck) < n:
                assert False

            res, self.deck = self.deck[:n], self.deck[n:]
            return res

        def score(self):
            """Total victory points of all owned cards."""
            cards = self.deck + self.discard
            return sum(card.victory for card in cards)

    def is_end(self):
        return (
            self.supply[card_types["province"]] == 0
            or list(self.supply.values()).count(0) >= 3
        )

    def play(self, player_i):
        player, player_state = self.players[player_i], self.player_states[player_i]

        player_state.num_turns += 1

        actions = 1
        buys = 1
        hand = player_state.get_cards(5)
        gold = sum(card.gold for card in hand)

        move_gen = player.play(self, player_state, hand, actions, buys, gold)

        first = True

        while True:
            try:
                if first:
                    move = next(move_gen)
                    first = False
                else:
                    move = move_gen.send((hand, actions, buys, gold))
            except StopIteration:
                break

            if isinstance(move, Buy):
                assert buys
                assert move.card.cost <= gold
                assert self.supply[move.card]
                self.supply[move.card] -= 1
                player_state.discard.append(move.card)
                buys -= 1
                gold -= move.card.cost
            else:
                assert False

        player_state.discard.extend(hand)

    def run(self):
        player_i = 0

        while not self.is_end():
            self.play(player_i)
            player_i = (player_i + 1) % len(self.players)

    def get_winners(self):
        """Return a list of winning player indices. More than one index
        indicates a draw.
        """
        scores = [(player.score(), -player.num_turns) for player in self.player_states]

        max_score = max(scores)

        return [i for i in range(len(self.players)) if scores[i] == max_score]


class Player(object):
    def play(self, game_state, player_state, hand, actions, buys, gold):
        """Decide what to do during a turn. This should yield Move objects
        indicating the moves to take, and a new (hand, actions, buys, gold)
        tuple will be passed in through this yield, indicating the state after
        the move.
        """
        raise NotImplementedError()


@attrs
class BigMoneyPlayerBasic(Player):
    """First attempt at a big money strategy; not competitive but interesting
    to test against."""

    desperation_thresh = attrib()

    def play(self, game_state, player_state, hand, actions, buys, gold):
        if gold >= 8:
            yield Buy(card_types["province"])
        elif gold >= 6 and game_state.supply[card_types["gold"]]:
            yield Buy(card_types["gold"])
        elif gold >= 3 and game_state.supply[card_types["silver"]]:
            yield Buy(card_types["silver"])
        elif game_state.supply[card_types["province"]] < self.desperation_thresh:
            for card in card_types["duchy"], card_types["estate"]:
                if card.cost <= gold:
                    yield Buy(card)
                    break


@attrs
class BigMoneyPlayerWiki(Player):
    """Big Money stratgget as per this:

        http://wiki.dominionstrategy.com/index.php/Big_Money

    If duchy_dance is True, then this rule is implemented, though this doesn't
    seem to improve the outcome for some reason:

        http://wiki.dominionstrategy.com/index.php/Penultimate_Province_Rule
    """

    duchy_dance = attrib(default=False)

    def play(self, game_state, player_state, hand, actions, buys, gold):
        all_cards = player_state.deck + player_state.discard + hand

        if (
            self.duchy_dance
            and gold > 5
            and (
                player_state.score()
                < max(st.score() for st in game_state.player_states)
            )
            and game_state.supply[card_types["province"]] == 2
            and game_state.supply[card_types["duchy"]]
        ):
            yield Buy(card_types["duchy"])

        elif gold >= 8:
            if (
                game_state.supply[card_types["gold"]]
                and all_cards.count(card_types["gold"]) == 0
                and all_cards.count(card_types["silver"]) < 5
            ):
                yield Buy(card_types["gold"])
            else:
                yield Buy(card_types["province"])

        elif (
            gold >= 6
            and game_state.supply[card_types["province"]] <= 4
            and game_state.supply[card_types["duchy"]]
        ):
            yield Buy(card_types["duchy"])
        elif gold >= 6 and game_state.supply[card_types["gold"]]:
            yield Buy(card_types["gold"])

        elif (
            gold >= 5
            and game_state.supply[card_types["province"]] <= 5
            and game_state.supply[card_types["duchy"]]
        ):
            yield Buy(card_types["duchy"])
        elif gold >= 5 and game_state.supply[card_types["silver"]]:
            yield Buy(card_types["silver"])

        elif (
            gold >= 3
            and game_state.supply[card_types["province"]] <= 2
            and game_state.supply[card_types["estate"]]
        ):
            yield Buy(card_types["estate"])
        elif gold >= 3 and game_state.supply[card_types["silver"]]:
            yield Buy(card_types["silver"])

        elif (
            gold >= 2
            and game_state.supply[card_types["province"]] <= 3
            and game_state.supply[card_types["estate"]]
        ):
            yield Buy(card_types["estate"])
