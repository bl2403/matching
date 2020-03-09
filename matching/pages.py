from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


class Introduction(Page):

    pass


class FirstRanking(Page):
    form_model = 'player'
    form_fields = ['first_choice_r1', 'second_choice_r1', 'third_choice_r1']

    def error_message(self, values):
        if values['first_choice_r1'] == values['second_choice_r1'] or values['first_choice_r1'] == values[
            'third_choice_r1'] or values['second_choice_r1'] == values['third_choice_r1']:
            return 'All three choices must be distinct'

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )

    def before_next_page(self):
        key = 'player_{}'.format(self.player.id_in_group)
        self.session.vars[key] = {
            'first_choice_r1': self.player.first_choice_r1,
            'second_choice_r1': self.player.second_choice_r1,
            'third_choice_r1': self.player.third_choice_r1,
        }


class ResultsWaitPage1(WaitPage):
    def after_all_players_arrive(self):
        pass


class AdviceAcceptance(Page):
    def is_displayed(self):
        return self.session.config['generation_number'] != '0'

    form_model = 'player'
    form_fields = ['advice_acceptance']


class AdviceValuationPage(Page):
    def is_displayed(self):
        return self.session.config['generation_number'] != '0' and self.player.advice_acceptance

    form_model = 'player'
    form_fields = ['one_advice', 'q1']

    def error_message(self, values):
        if len(values['q1']) != 10:  # why is the length 10?!!
            return 'You must choose exactly two advice sources.'

    def vars_for_template(self):
        gen_number = int(self.session.config['generation_number'])
        even_odd = gen_number % 2
        return{
            'parity': even_odd
        }


class ResultsWaitPage2(WaitPage):
    def is_displayed(self):
        return self.session.config['generation_number'] != '0'

    def after_all_players_arrive(self):
        self.group.advice_reception()


class AdviceReceivingPage(Page):
    def is_displayed(self):
        return self.session.config['generation_number'] != '0' and self.player.advice_acceptance

    def vars_for_template(self):
        return {
            'intro_1': self.player.intro_1,
            'intro_2': self.player.intro_2,
            'intro_3': self.player.intro_3,
            'num_adv': self.player.num_adv,
            'first_advice': self.player.first_advice,
            'first_verbal': self.player.first_verbal,
            'second_advice': self.player.second_advice,
            'second_verbal': self.player.second_verbal,
            'third_advice': self.player.third_advice,
            'third_verbal': self.player.third_verbal
        }

    # timeout_seconds = 300


class SecondRanking(Page):
    form_model = 'player'
    form_fields = ['first_choice_r2', 'second_choice_r2', 'third_choice_r2']

    def error_message(self, values):
        if values['first_choice_r2'] == values['second_choice_r2'] or values['first_choice_r2'] == values[
            'third_choice_r2'] or values['second_choice_r2'] == values['third_choice_r2']:
            return 'The three choices must be distinct'

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            gen_num=self.session.config['generation_number'],
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right,
            intro_1=self.player.intro_1,
            intro_2=self.player.intro_2,
            intro_3=self.player.intro_3,
            num_adv=self.player.num_adv,
            first_advice=self.player.first_advice,
            first_verbal=self.player.first_verbal,
            second_advice=self.player.second_advice,
            second_verbal=self.player.second_verbal,
            third_advice=self.player.third_advice,
            third_verbal=self.player.third_verbal
        )

    def before_next_page(self):
        key = 'player_{}'.format(self.player.id_in_group)
        self.session.vars[key].update(
            {
                'first_choice_r2': self.player.first_choice_r2,
                'second_choice_r2': self.player.second_choice_r2,
                'third_choice_r2': self.player.third_choice_r2
            }
        )


class ResultsWaitPage3(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoff()
        self.group.set_advisor_payoff()


class Results(Page):
    def vars_for_template(self):
        if self.player.final_payoff == Constants.high_payoff:
            fav = ""
        elif self.player.final_payoff == Constants.medium_payoff:
            fav = "second"
        else:
            fav = "third"

        return dict(
            matching_1=self.player.match_1,
            matching_2=self.player.match_2,
            favorite=fav,
            payoff=self.player.final_payoff,
            paying_round=self.group.paying_round
        )


class Introduction2(Page):
    pass


class AdviceGivingPage1(Page):
    form_model = 'player'
    form_fields = ['advice_1', 'verbal_1']

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )


class AdviceGivingPage2(Page):
    form_model = 'player'
    form_fields = ['advice_2', 'verbal_2']

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )


class AdviceGivingPage3(Page):
    form_model = 'player'
    form_fields = ['advice_3', 'verbal_3']

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )


class AdviceGivingPage4(Page):
    form_model = 'player'
    form_fields = ['advice_4', 'verbal_4']

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any objects"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any objects"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )


class AdviceGivingPage5(Page):
    form_model = 'player'
    form_fields = ['advice_5', 'verbal_5']

    def vars_for_template(self):
        if self.player.id_in_group == 1:
            priority_right = "You receive priority rights from object C"
            preference = "C over A over B"

        elif self.player.id_in_group == 2:
            priority_right = "You receive priority rights from object A"
            preference = "C over A over B"

        elif self.player.id_in_group == 3:
            priority_right = "You receive priority rights from object B"
            preference = "C over B over A"

        elif self.player.id_in_group == 4:
            priority_right = "You do not have priority rights from any object"
            preference = "A over B over C"
        else:
            priority_right = "You do not have priority rights from any object"
            preference = "A over C over B"

        return dict(
            preference_type=self.player.id_in_group,
            player_preference=preference,
            player_priority_right=priority_right
        )

    def before_next_page(self):
        key = 'player_{}'.format(self.player.id_in_group)
        self.session.vars[key].update({
            'advice_1': self.player.advice_1,
            'verbal_1': self.player.verbal_1,
            'advice_2': self.player.advice_2,
            'verbal_2': self.player.verbal_2,
            'advice_3': self.player.advice_3,
            'verbal_3': self.player.verbal_3,
            'advice_4': self.player.advice_4,
            'verbal_4': self.player.verbal_4,
            'advice_5': self.player.advice_5,
            'verbal_5': self.player.verbal_5
        })


class Introduction3(Page):
    pass


class PersonalInfo(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'grade', 'major']


class RAQuizPage(Page):
    form_model = 'player'
    form_fields = ['ra_1', 'ra_2', 'ra_3', 'ra_4', 'ra_5', 'ra_6', 'ra_7', 'ra_8', 'ra_9', 'ra_10']


class CognitiveReflectionTest(Page):
    form_model = 'player'
    form_fields = ['crt_bat', 'crt_widget', 'crt_lake']


class End(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_advice()
        self.group.simulation()


page_sequence = [
    Introduction,
    FirstRanking,
    ResultsWaitPage1,
    AdviceAcceptance,
    AdviceValuationPage,
    ResultsWaitPage2,
    AdviceReceivingPage,
    SecondRanking,
    ResultsWaitPage3,
    Results,
    Introduction2,
    AdviceGivingPage1,
    AdviceGivingPage2,
    AdviceGivingPage3,
    AdviceGivingPage4,
    AdviceGivingPage5,
    Introduction3,
    PersonalInfo,
    RAQuizPage,
    CognitiveReflectionTest,
    End,
]
