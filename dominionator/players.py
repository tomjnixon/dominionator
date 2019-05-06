from attr import attrs, attrib
from .sim import card_types, Buy, Player


@attrs
class BigMoneyPlayerBasic(Player):
    """First attempt at a big money strategy; not competitive but interesting
    to test against."""

    desperation_thresh = attrib()

    def play(self, game_state, player_state, turn_state):
        if turn_state.gold >= 8:
            yield Buy(card_types["province"])
        elif turn_state.gold >= 6 and game_state.supply[card_types["gold"]]:
            yield Buy(card_types["gold"])
        elif turn_state.gold >= 3 and game_state.supply[card_types["silver"]]:
            yield Buy(card_types["silver"])
        elif game_state.supply[card_types["province"]] < self.desperation_thresh:
            for card in card_types["duchy"], card_types["estate"]:
                if card.cost <= turn_state.gold:
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

    def play(self, game_state, player_state, turn_state):
        while turn_state.buys:
            to_buy = self.get_buy(game_state, player_state, turn_state)
            if to_buy is None:
                break

            turn_state = (yield Buy(to_buy))

    def get_buy(self, game_state, player_state, turn_state):
        all_cards = player_state.deck + player_state.discard + turn_state.hand

        if (
            self.duchy_dance
            and turn_state.gold > 5
            and (
                player_state.score()
                < max(st.score() for st in game_state.player_states)
            )
            and game_state.supply[card_types["province"]] == 2
            and game_state.supply[card_types["duchy"]]
        ):
            return card_types["duchy"]

        elif turn_state.gold >= 8:
            if (
                game_state.supply[card_types["gold"]]
                and all_cards.count(card_types["gold"]) == 0
                and all_cards.count(card_types["silver"]) < 5
            ):
                return card_types["gold"]
            elif game_state.supply[card_types["province"]]:
                return card_types["province"]

        elif (
            turn_state.gold >= 6
            and game_state.supply[card_types["province"]] <= 4
            and game_state.supply[card_types["duchy"]]
        ):
            return card_types["duchy"]
        elif turn_state.gold >= 6 and game_state.supply[card_types["gold"]]:
            return card_types["gold"]

        elif (
            turn_state.gold >= 5
            and game_state.supply[card_types["province"]] <= 5
            and game_state.supply[card_types["duchy"]]
        ):
            return card_types["duchy"]
        elif turn_state.gold >= 5 and game_state.supply[card_types["silver"]]:
            return card_types["silver"]

        elif (
            turn_state.gold >= 3
            and game_state.supply[card_types["province"]] <= 2
            and game_state.supply[card_types["estate"]]
        ):
            return card_types["estate"]
        elif turn_state.gold >= 3 and game_state.supply[card_types["silver"]]:
            return card_types["silver"]

        elif (
            turn_state.gold >= 2
            and game_state.supply[card_types["province"]] <= 3
            and game_state.supply[card_types["estate"]]
        ):
            return card_types["estate"]


@attrs
class BigMoneyMine(BigMoneyPlayerWiki):
    priority = attrib(
        default=[
            (card_types["copper"], card_types["silver"]),
            (card_types["silver"], card_types["gold"]),
        ]
    )

    def play(self, game_state, player_state, turn_state):
        all_cards = player_state.deck + player_state.discard + turn_state.hand

        if card_types["mine"] in turn_state.hand:
            for from_card, to_card in self.priority:
                if from_card in turn_state.hand and game_state.supply[to_card]:
                    yield card_types["mine"].action(from_card, to_card)
                    break

        if (
            6 > turn_state.gold >= 5
            and all_cards.count(card_types["mine"]) < 1
            and game_state.supply[card_types["mine"]]
        ):
            yield Buy(card_types["mine"])
        else:
            yield from super(BigMoneyMine, self).play(
                game_state, player_state, turn_state
            )


@attrs
class BigMoneyPlus(BigMoneyPlayerWiki):
    cards = attrib(default=[])

    @attrs
    class CardToBuy(object):
        card = attrib()
        number = attrib(default=1)
        pay_over = attrib(default=0)

    def play(self, game_state, player_state, turn_state):
        all_cards = player_state.deck + player_state.discard + turn_state.hand

        # play any action cards
        for to_buy in self.cards:
            while turn_state.actions and to_buy.card in turn_state.hand:
                # print(turn_state.actions)
                turn_state = (yield to_buy.card.action())

        # buy any action cards
        for to_buy in self.cards:
            if (
                turn_state.buys
                and game_state.supply[to_buy.card]
                and (
                    to_buy.card.cost
                    <= turn_state.gold
                    <= to_buy.card.cost + to_buy.pay_over
                )
            ):
                turn_state = (yield Buy(to_buy.card))

        yield from super(BigMoneyPlus, self).play(game_state, player_state, turn_state)
