from attr import attrs, attrib
from .sim import card_types, Buy, Player


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
