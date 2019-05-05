from attr import attrs, attrib, Factory, evolve
from random import shuffle
from collections import OrderedDict, defaultdict
from enum import Enum, auto
from .list_utils import removed


class Move(object):
    pass


@attrs(frozen=True)
class Action(Move):
    action_card = attrib()

    def run(self, game_state, player_state, turn_state):
        assert turn_state.phase == Game.TurnPhase.ACTION
        assert turn_state.actions
        player_state.discard.append(self.action_card)
        return evolve(
            turn_state,
            actions=turn_state.actions - 1,
            hand=removed(turn_state.hand, self.action_card),
        )


@attrs(frozen=True)
class Card(object):
    name = attrib()
    cost = attrib()

    gold = attrib(default=0)

    victory = attrib(default=0)


@attrs(frozen=True)
class BasicActionCard(Card):
    add_actions = attrib(default=0)
    add_buys = attrib(default=0)
    add_gold = attrib(default=0)
    add_cards = attrib(default=0)

    def action(self):
        return self.BasicAction(self)

    @attrs(frozen=True)
    class BasicAction(Action):
        def run(self, game_state, player_state, turn_state):
            turn_state = super(BasicActionCard.BasicAction, self).run(
                game_state, player_state, turn_state
            )

            return evolve(
                turn_state,
                hand=turn_state.hand
                + player_state.get_cards(self.action_card.add_cards),
                actions=turn_state.actions + self.action_card.add_actions,
                buys=turn_state.buys + self.action_card.add_buys,
                additional_gold=turn_state.additional_gold + self.action_card.add_gold,
            )


class Mine(Card):
    @classmethod
    def make(cls):
        return cls("mine", 5)

    def action(self, from_card, to_card):
        return self.MineAction(self, from_card, to_card)

    @attrs(frozen=True)
    class MineAction(Action):
        from_card = attrib()
        to_card = attrib()

        def run(self, game_state, player_state, turn_state):
            turn_state = super(Mine.MineAction, self).run(
                game_state, player_state, turn_state
            )

            assert self.to_card.cost <= self.from_card.cost + 3

            return evolve(
                turn_state,
                hand=removed(turn_state.hand, self.from_card) + [self.to_card],
            )


_card_types = [
    Card("estate", 2, victory=1),
    Card("duchy", 5, victory=3),
    Card("province", 8, victory=6),
    Card("copper", 0, gold=1),
    Card("silver", 3, gold=2),
    Card("gold", 6, gold=3),
    Mine.make(),
    BasicActionCard("festival", 5, add_actions=2, add_buys=1, add_gold=2),
    BasicActionCard("smithy", 4, add_cards=3),
]

card_types = OrderedDict((card.name, card) for card in _card_types)


@attrs
class Buy(Move):
    card = attrib()

    def run(self, game_state, player_state, turn_state):
        assert turn_state.buys
        assert self.card.cost <= turn_state.gold
        assert game_state.supply[self.card]

        game_state.supply[self.card] -= 1
        player_state.discard.append(self.card)
        return evolve(
            turn_state,
            phase=Game.TurnPhase.BUY,
            buys=turn_state.buys - 1,
            additional_gold=turn_state.additional_gold - self.card.cost,
        )


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
            ("mine", 8),
            ("festival", 8),
            ("smithy", 8),
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

    class TurnPhase(Enum):
        ACTION = auto()
        BUY = auto()

    @attrs(frozen=True)
    class TurnState(object):
        hand = attrib()
        phase = attrib(default=Factory(lambda: Game.TurnPhase.ACTION))
        actions = attrib(default=1)
        buys = attrib(default=1)
        additional_gold = attrib(default=0)

        @property
        def gold(self):
            return sum(card.gold for card in self.hand) + self.additional_gold

    def is_end(self):
        return (
            self.supply[card_types["province"]] == 0
            or list(self.supply.values()).count(0) >= 3
        )

    def play(self, player_i):
        player, player_state = self.players[player_i], self.player_states[player_i]

        player_state.num_turns += 1

        hand = player_state.get_cards(5)
        turn_state = self.TurnState(hand=hand)

        move_gen = player.play(self, player_state, turn_state)

        first = True

        while True:
            try:
                if first:
                    move = next(move_gen)
                    first = False
                else:
                    move = move_gen.send((turn_state))
            except StopIteration:
                break

            turn_state = move.run(self, player_state, turn_state)

        player_state.discard.extend(turn_state.hand)

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
    def play(self, game_state, player_state, turn_state):
        """Decide what to do during a turn. This should yield Move objects
        indicating the moves to take, and a new (hand, actions, buys, gold)
        tuple will be passed in through this yield, indicating the state after
        the move.
        """
        raise NotImplementedError()
