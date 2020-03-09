from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from django import forms

import os
import random
import json
import logging

import boto3


author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'matching'
    players_per_group = 5
    num_rounds = 1

    instructions_template = 'matching/instructions.html'
    instructions_template_1 = 'matching/instructions1.html'
    instructions_template_2 = 'matching/instructions2.html'
    instructions_template_3 = 'matching/instructions3.html'
    instructions_template_4 = 'matching/instructions4.html'
    instructions_template_5 = 'matching/instructions5.html'

    Schools = [
        'A',
        'B',
        'C'
    ]

    School_Capacity = [
        1,
        2,
        2,
    ]

    Preferences = [
        ['C', 'A', 'B'],
        ['C', 'A', 'B'],
        ['C', 'B', 'A'],
        ['A', 'B', 'C'],
        ['A', 'C', 'B']
    ]

    Priority_Rights = [
        'C',
        'A',
        'B',
    ]

    Student_Priority_Rights = [
        1,
        2,
        0,
    ]

    Advice_Sources_1 = [
        'Same-type Advice',
        'Other-type Advice',
        'Third-party Advice',
    ]

    Advice_Sources_2 = [
        'Same-type Advice & Other-type Advice',
        'Other-type Advice & Third-party Advice',
        'Same-type Advice & Third-party Advice',
    ]

    rankings = [
        'A, B, C',
        'A, C, B',
        'B, A, C',
        'B, C, A',
        'C, A, B',
        'C, B, A',
    ]
    advice_description = [
        'This is a piece of advice given by the subject of the same preference type as you from the previous session.',
        'This is a piece of advice given by a subject of a different preference type as you from the previous session.',
        'The following is an example of advice often given by matching administrators, such as the Department of '
        'Education of a particular city.',
        # 'The following is an example of advice often found in a newspaper or by word of mouth or an online forum.'
    ]

    lottery = [1, 2, 3, 4, 5]

    high_payoff = 24
    medium_payoff = 16
    low_payoff = 8


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.session.config['generation_number'] == '0':
            pass
        else:
            # logger = logging.getLogger(__name__)
            # Reading in the advice from Amazon s3
            BUCKET = os.environ.get('AWS_STORAGE_BUCKET_NAME')
            FILE_TO_READ = 'generation.json'
            client = boto3.client('s3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

            result = client.get_object(Bucket=BUCKET, Key=FILE_TO_READ)
            text = result["Body"].read().decode()
            all_advice = json.loads(text)

            if self.round_number == 1:
                for index, player in enumerate(self.get_players()):
                    player.participant.vars['all_advice'] = all_advice

            # BASE_DIR = os.path.dirname(os.path.dirname(__file__))
            # file_name = 'generation_{}.json'.format(int(self.session.config['generation_number'])-1)
            # generation_file = os.path.join(os.path.dirname(BASE_DIR), "matching", "advice", file_name)
            # try:
            #     with open(generation_file) as file:
            #         all_advice = json.load(file)
            #
            #         if self.round_number == 1:
            #             for index, player in enumerate(self.get_players()):
            #                 player.participant.vars['all_advice'] = all_advice
            # except FileNotFoundError as e:
            #     logger.error('Unable to open generation file. {}'.format(e))

        # all_advice = []
        #
        # for i in range(Constants.players_per_group):
        #     advice_to_others = {}
        #
        #     for j in range(Constants.players_per_group):
        #         advice_to_others['advice_{}'.format(j)] = self.session.config['advice_{}{}'.format(i, j)]
        #         advice_to_others['verbal_{}'.format(j)] = self.session.config['verbal_{}{}'.format(i, j)]
        #
        #     all_advice.append(advice_to_others)
        #
        # print(all_advice)


class Group(BaseGroup):
    paying_round = models.IntegerField()

    def matching(self, rankings):
        # rankings is a list of lists, where the first entry is the submitted ranking of the type 1 subject
        # Tie breaker
        lottery = [1, 2, 3, 4, 5]
        random.shuffle(lottery)

        temp_match = [0, 0, 0, 0, 0]  # Initial temporary match
        status = [1, 1, 1, 1, 1]  # The current application status of the players. 1 if considered by 1st choice, etc.

        while 0 in temp_match:
            indices = [k for k, x in enumerate(temp_match) if temp_match[k] == 0]  # all unmatched students
            # print(indices)

            # check application for every school
            for i in range(0, 3):
                # students already matched to the school
                temp_matched = [k for k, x in enumerate(temp_match) if temp_match[k] == Constants.Schools[i]]
                # print(temp_matched)
                # rejected students who applied to the school in the current round
                apps = [k for k in indices if rankings[k][status[k] - 1] ==
                        Constants.Schools[i]]

                apps.extend(temp_matched)

                # combine the applicants with their lotteries
                pairs = [[lottery[apps[l]], apps[l]] for l in range(0, len(apps))]
                pairs.sort()
                # order of acceptance
                new_apps = [pairs[m][1] for m in range(0, len(apps))]

                # If school does not reach full capacity
                if len(apps) <= Constants.School_Capacity[i]:
                    for j in apps:
                        temp_match[j] = Constants.Schools[i]

                # If school reaches full capacity
                else:
                    # Case 1: Student with priority applies
                    if Constants.Student_Priority_Rights[i] in new_apps:
                        # The student with priority right is first accepted
                        temp_match[Constants.Student_Priority_Rights[i]] = Constants.Schools[i]
                        new_apps.remove(Constants.Student_Priority_Rights[i])
                        # Students without priority but high in ranking gets accepted
                        for j in new_apps[:Constants.School_Capacity[i] - 1]:
                            temp_match[j] = Constants.Schools[i]
                        # The rest is is rejected
                        for j in new_apps[Constants.School_Capacity[i] - 1:]:
                            status[j] = status[j] + 1

                    # Case 2: Student with priority does not apply
                    else:
                        # The first 1 or 2 students are accepted
                        for j in new_apps[:Constants.School_Capacity[i]]:
                            temp_match[j] = Constants.Schools[i]
                        # The rest are rejected
                        for j in new_apps[Constants.School_Capacity[i]:]:
                            status[j] = status[j] + 1

        return temp_match

    def advice_reception(self):

        for i in range(Constants.players_per_group):
            # Determine the number of advice
            p = self.get_player_by_id(i+1)
            if p.advice_acceptance:
                p.num_adv = random.randint(1, 3)
            else:
                p.num_adv = 0

            # Should the subject receive advice from other types, determine the advice giver type
            other_types = []
            for k in range(Constants.players_per_group):
                if k != i:
                    other_types.append(k)
            advice_giver = random.choice(other_types)

            # Should the subject receive third-party advice
            third_party_advice = Constants.Preferences[i][0] + ", " + Constants.Preferences[i][1] + ", " \
                                                                                                    "" + \
                                 Constants.Preferences[i][2]

            # Advice Description
            p.intro_1 = ''
            p.intro_2 = ''
            p.intro_3 = ''

            p.first_advice = ''
            p.first_verbal = ''
            p.second_advice = ''
            p.second_verbal = ''
            p.third_advice = ''
            p.third_verbal = ''

            # Assign advice
            if p.advice_acceptance:
                # Receive only one piece of advice
                if p.num_adv == 1:
                    if p.one_advice == Constants.Advice_Sources_1[0]:
                        p.first_advice = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["advice"]
                        p.first_verbal = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["verbal"]
                        p.intro_1 = Constants.advice_description[0]
                        p.advice_giver_1 = int(p.id_in_group)
                    elif p.one_advice == Constants.Advice_Sources_1[1]:
                        p.first_advice = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["advice"]
                        p.first_verbal = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["verbal"]
                        p.intro_1 = Constants.advice_description[1]
                        p.advice_giver_1 = advice_giver+1
                    else:
                        p.first_advice = third_party_advice
                        p.first_verbal = self.session.config['third_party']

                        p.intro_1 = Constants.advice_description[2]

                elif p.num_adv == 2:
                    print(p.q1)
                    print(p.q1[2])
                    print(p.q1[7])

                    if p.q1[2] == '1' and p.q1[7] == '2':
                        p.first_advice = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["advice"]
                        p.first_verbal = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["verbal"]
                        p.intro_1 = Constants.advice_description[0]
                        p.advice_giver_1 = p.id_in_group

                        p.second_advice = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["advice"]
                        p.second_verbal = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["verbal"]
                        p.intro_2 = Constants.advice_description[1]
                        p.advice_giver_2 = advice_giver + 1
                    elif p.q1[2] == '2' and p.q1[7] == '3':
                        p.first_advice = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["advice"]
                        p.first_verbal = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["verbal"]
                        p.intro_1 = Constants.advice_description[1]
                        p.advice_giver_1 = advice_giver+1

                        p.second_advice = third_party_advice
                        p.second_verbal = self.session.config['third_party']
                        p.intro_2 = Constants.advice_description[2]

                    else:
                        p.first_advice = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["advice"]
                        p.first_verbal = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["verbal"]
                        p.intro_1 = Constants.advice_description[0]
                        p.advice_giver_1 = p.id_in_group

                        p.second_advice = third_party_advice
                        p.second_verbal = self.session.config['third_party']
                        p.intro_2 = Constants.advice_description[2]
                else:
                    p.first_advice = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["advice"]
                    p.first_verbal = p.participant.vars['all_advice'][str(i+1)][str(i+1)]["verbal"]
                    p.intro_1 = Constants.advice_description[0]
                    p.advice_giver_1 = p.id_in_group

                    p.second_advice = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["advice"]
                    p.second_verbal = p.participant.vars['all_advice'][str(advice_giver + 1)][str(i+1)]["verbal"]
                    p.intro_2 = Constants.advice_description[1]
                    p.advice_giver_2 = advice_giver+1

                    p.third_advice = third_party_advice
                    p.third_verbal = self.session.config['third_party']
                    p.intro_3 = Constants.advice_description[2]

    def set_payoff(self):
        players = self.get_players()
        rankings_r1 = [[i.first_choice_r1, i.second_choice_r1, i.third_choice_r1] for i in players]
        rankings_r2 = [[i.first_choice_r2, i.second_choice_r2, i.third_choice_r2] for i in players]
        m1 = self.matching(rankings_r1)
        m2 = self.matching(rankings_r2)

        for i in range(0, 5):
            players[i].match_1 = m1[i]
            players[i].match_2 = m2[i]

            # define payoff_1, payoff_2
            if players[i].match_1 == Constants.Preferences[i][0]:
                players[i].payoff_1 = Constants.high_payoff
            elif players[i].match_1 == Constants.Preferences[i][1]:
                players[i].payoff_1 = Constants.medium_payoff
            else:
                players[i].payoff_1 = Constants.low_payoff

            if players[i].match_2 == Constants.Preferences[i][0]:
                players[i].payoff_2 = Constants.high_payoff
            elif players[i].match_2 == Constants.Preferences[i][1]:
                players[i].payoff_2 = Constants.medium_payoff
            else:
                players[i].payoff_2 = Constants.low_payoff

            payoff_r1 = [i.payoff_1 for i in players]
            payoff_r2 = [i.payoff_2 for i in players]

        # Random Paying Round
        self.paying_round = random.randint(1, 2)

        # Final payoff
        for i in range(0, 5):
            if self.paying_round == 1:
                players[i].final_payoff = payoff_r1[i]
            else:
                players[i].final_payoff = payoff_r2[i]

            players[i].final_payoff_in_dollars = players[i].final_payoff * 0.8

    def set_advisor_payoff(self):
        for i in range(1, Constants.players_per_group+1):
            advice_receivers = []
            player = self.get_player_by_id(i)
            for j in range(1, Constants.players_per_group+1):
                p = self.get_player_by_id(j)
                if p.advice_giver_1 == i or p.advice_giver_2 == i:
                    advice_receivers.append(j)
            if len(advice_receivers) != 0:
                successor = random.choice(advice_receivers)
                player.payoff_for_predecessor = self.get_player_by_id(successor).final_payoff*0.5
            else:
                player.payoff_for_predecessor = 0.0

            player.payoff_for_predecessor_in_dollars = player.payoff_for_predecessor * 0.8

    def simulation(self):
        all_decision_r1 = [0, 0, 0, 0, 0]
        all_decision_r2 = [0, 0, 0, 0, 0]

        for player_id in range(1, Constants.players_per_group + 1):
            player_key = 'player_{}'.format(player_id)
            all_decision_r1[player_id-1] = [
                self.session.vars[player_key]["first_choice_r1"],
                self.session.vars[player_key]["second_choice_r1"],
                self.session.vars[player_key]["third_choice_r1"],
            ]
            all_decision_r2[player_id-1] = [
                self.session.vars[player_key]["first_choice_r2"],
                self.session.vars[player_key]["second_choice_r2"],
                self.session.vars[player_key]["third_choice_r2"],
            ]

        counter = 0
        welfare_before_advice = [0.0, 0.0, 0.0, 0.0, 0.0]
        welfare_after_advice = [0.0, 0.0, 0.0, 0.0, 0.0]

        while counter < 1000:
            sim_matching_r1 = self.matching(all_decision_r1)
            sim_matching_r2 = self.matching(all_decision_r2)

            print(sim_matching_r1)
            print(sim_matching_r2)

            for i in range(0, len(sim_matching_r1)):
                if sim_matching_r1[i] == Constants.Preferences[i][0]:
                    welfare_before_advice[i] = welfare_before_advice[i] + 24.0
                elif sim_matching_r1[i] == Constants.Preferences[i][1]:
                    welfare_before_advice[i] = welfare_before_advice[i] + 16.0
                else:
                    welfare_before_advice[i] = welfare_before_advice[i] + 8.0

            for i in range(0, len(sim_matching_r2)):
                if sim_matching_r2[i] == Constants.Preferences[i][0]:
                    welfare_after_advice[i] = welfare_after_advice[i] + 24.0
                elif sim_matching_r2[i] == Constants.Preferences[i][1]:
                    welfare_after_advice[i] = welfare_after_advice[i] + 16.0
                else:
                    welfare_after_advice[i] = welfare_after_advice[i] + 8.0

            counter = counter + 1

        for i in range(0, Constants.players_per_group):
            self.get_player_by_id(i+1).average_welfare_before_advice = welfare_before_advice[i]/1000
            self.get_player_by_id(i+1).average_welfare_after_advice = welfare_after_advice[i]/1000

    def set_advice(self):
        all_advice = {}
        for player_id in range(1, Constants.players_per_group + 1):
            player_key = 'player_{}'.format(player_id)
            all_advice[str(player_id)] = {
                "1": {
                    "advice": self.session.vars[player_key]["advice_1"],
                    "verbal": self.session.vars[player_key]["verbal_1"]
                },
                "2": {
                    "advice": self.session.vars[player_key]["advice_2"],
                    "verbal": self.session.vars[player_key]["verbal_2"]
                },
                "3": {
                    "advice": self.session.vars[player_key]["advice_3"],
                    "verbal": self.session.vars[player_key]["verbal_3"]
                },
                "4": {
                    "advice": self.session.vars[player_key]["advice_4"],
                    "verbal": self.session.vars[player_key]["verbal_4"]
                },
                "5": {
                    "advice": self.session.vars[player_key]["advice_5"],
                    "verbal": self.session.vars[player_key]["verbal_5"]
                },
            }

        # Write Json to Amazon s3
        BUCKET = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        FILE_TO_READ = 'generation.json'
        client = boto3.client('s3',
                              aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

        response = client.put_object(Bucket=BUCKET, Body=json.dumps(all_advice), Key=FILE_TO_READ)
        print(response)


        # BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        # file_name = 'generation_{}.json'.format(int(self.session.config['generation_number']))
        # generation_file = os.path.join(os.path.dirname(BASE_DIR), "matching", "advice", file_name)
        # try:
        #     with open(generation_file, 'w') as file:
        #         file.write(json.dumps(all_advice))
        # except IOError as e:
        #     print("Error writing json file: {}".format(e))


class Player(BasePlayer):

    # For school choice problem first round
    first_choice_r1 = models.StringField(
        choices=Constants.Schools,
        doc="""Student's first choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )
    second_choice_r1 = models.StringField(
        choices=Constants.Schools,
        doc="""student's second choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )
    third_choice_r1 = models.StringField(
        choices=Constants.Schools,
        doc="""Student's third choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )

    # For advice acceptance
    advice_acceptance = models.BooleanField()

    # Number of advice
    num_adv = models.IntegerField()

    # For advice valuation
    one_advice = models.StringField(
        choices=Constants.Advice_Sources_1,
        doc="""Should the student receive one piece of advice""",
        widget=widgets.RadioSelect,
    )

    q1 = models.StringField(widget=forms.CheckboxSelectMultiple(choices=(("1", ""), ("2", ""), ("3", ""))))

    # For advice assignment
    first_advice = models.StringField()
    first_verbal = models.StringField()

    second_advice = models.StringField()
    second_verbal = models.StringField()

    third_advice = models.StringField()
    third_verbal = models.StringField()

    intro_1 = models.StringField()
    intro_2 = models.StringField()
    intro_3 = models.StringField()

    # Identify advice giver
    advice_giver_1 = models.IntegerField()
    advice_giver_2 = models.IntegerField()

    # For school choice problem second round
    first_choice_r2 = models.StringField(
        choices=Constants.Schools,
        doc="""Student's first choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )
    second_choice_r2 = models.StringField(
        choices=Constants.Schools,
        doc="""student's second choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )
    third_choice_r2 = models.StringField(
        choices=Constants.Schools,
        doc="""Student's third choice in submitted ranking""",
        widget=widgets.RadioSelectHorizontal,
    )

    # For payoff setting
    payoff_1 = models.FloatField()
    payoff_2 = models.FloatField()
    payoff_for_predecessor = models.FloatField()
    payoff_for_predecessor_in_dollars = models.FloatField()

    # For results
    final_payoff = models.FloatField()
    final_payoff_in_dollars = models.FloatField()
    match_1 = models.StringField()
    match_2 = models.StringField()

    # Simulation Results
    average_welfare_before_advice = models.FloatField()
    average_welfare_after_advice = models.FloatField()

    # For advice giving
    advice_1 = models.StringField(
        choices=Constants.rankings,
        doc="""suggested strategy for type 1""",
        label="What is your suggested strategy for a subject with preferences over the objects as C A B and priority "
              "right from object C",
        widget=widgets.RadioSelectHorizontal,
    )
    advice_2 = models.StringField(
        choices=Constants.rankings,
        doc="""suggested strategy for type 2""",
        label="What is your suggested strategy for a subject with preferences over the objects as C A B and priority "
              "right from object A",
        widget=widgets.RadioSelectHorizontal,
    )
    advice_3 = models.StringField(
        choices=Constants.rankings,
        doc="""suggested strategy for type 3""",
        label="What is your suggested strategy for a subject with preferences over objects as C B A and priority "
              "right from object B?",
        widget=widgets.RadioSelectHorizontal,
    )
    advice_4 = models.StringField(
        choices=Constants.rankings,
        doc="""suggested strategy for type 4""",
        label="What is your suggested strategy for a subject with preferences over objects as A B C but without "
              "priority rights from any object?",
        widget=widgets.RadioSelectHorizontal,
    )
    advice_5 = models.StringField(
        choices=Constants.rankings,
        doc="""suggested strategy for type 5""",
        label="What is your suggested strategy for a subject with preferences over objects as A C B but without "
              "priority rights from any object?",
        widget=widgets.RadioSelectHorizontal,
    )

    verbal_1 = models.LongStringField(
        label="What is your reasoning for your suggested strategy above?"
    )
    verbal_2 = models.LongStringField(
        label="What is your reasoning for your suggested strategy above?"
    )
    verbal_3 = models.LongStringField(
        label="What is your reasoning for your suggested strategy above?"
    )
    verbal_4 = models.LongStringField(
        label="What is your reasoning for your suggested strategy above?"
    )
    verbal_5 = models.LongStringField(
        label="What is your reasoning for your suggested strategy above?"
    )

    # For personal information
    age = models.IntegerField(
        label='What is your age?',
        min=13, max=125)
    gender = models.StringField(
        choices=['Male', 'Female', 'Other'],
        label='What is your gender?',
        widget=widgets.RadioSelect)
    grade = models.StringField(
        choices=['Freshman', 'Sophomore', 'Junior', 'Senior'],
        label='What class are you in?',
        widget=widgets.RadioSelect,
    )
    major = models.StringField(
        label='What is your major?'
    )

    # For cognitive reflection test
    crt_bat = models.IntegerField(
        label='''
            A bat and a ball cost 22 dollars in total.
            The bat costs 20 dollars more than the ball.
            How many dollars does the ball cost?'''
    )

    crt_widget = models.IntegerField(
        label='''
            "If it takes 5 machines 5 minutes to make 5 widgets,
            how many minutes would it take 100 machines to make 100 widgets?"
            '''
    )

    crt_lake = models.IntegerField(
        label='''
            In a lake, there is a patch of lily pads.
            Every day, the patch doubles in size.
            If it takes 48 days for the patch to cover the entire lake,
            how many days would it take for the patch to cover half of the lake?
            '''
    )
    crt_race = models.IntegerField(
        label='''If you are running a race and you pass the person in the second place, what place are you in? Use 
        integer to express your answer.
        '''
    )

    # For measuring subjects' risk aversion, taken from Holt and Laury (2002)
    ra_1 = models.StringField(
        choices=[
            '0.1 chance of getting 2.00 ECU and 0.9 chance of getting 1.60 ECU',
            '0.1 chance of getting 3.85 ECU and 0.9 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_2 = models.StringField(
        choices=[
            '0.2 chance of getting 2.00 ECU and 0.8 chance of getting 1.60 ECU',
            '0.2 chance of getting 3.85 ECU and 0.8 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_3 = models.StringField(
        choices=[
            '0.3 chance of getting 2.00 ECU and 0.7 chance of getting 1.60 ECU',
            '0.3 chance of getting 3.85 ECU and 0.7 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_4 = models.StringField(
        choices=[
            '0.4 chance of getting 2.00 ECU and 0.6 chance of getting 1.60 ECU',
            '0.4 chance of getting 3.85 ECU and 0.6 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_5 = models.StringField(
        choices=[
            '0.5 chance of getting 2.00 ECU and 0.5 chance of getting 1.60 ECU',
            '0.5 chance of getting 3.85 ECU and 0.5 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_6 = models.StringField(
        choices=[
            '0.6 chance of getting 2.00 ECU and 0.4 chance of getting 1.60 ECU',
            '0.6 chance of getting 3.85 ECU and 0.4 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_7 = models.StringField(
        choices=[
            '0.7 chance of getting 2.00 ECU and 0.3 chance of getting 1.60 ECU',
            '0.7 chance of getting 3.85 ECU and 0.3 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_8 = models.StringField(
        choices=[
            '0.8 chance of getting 2.00 ECU and 0.2 chance of getting 1.60 ECU',
            '0.8 chance of getting 3.85 ECU and 0.2 chance of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_9 = models.StringField(
        choices=[
            '0.9 probability of getting 2.00 ECU and 0.1 probability of getting 1.60 ECU',
            '0.9 probability of getting 3.85 ECU and 0.1 probability of getting 0.10 ECU',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )

    ra_10 = models.StringField(
        choices=[
            'Getting 2.00 ECU for sure and not getting 1.60 ECU for sure',
            'Getting 3.85 ECU for sure and not getting 0.10 ECU for sure',
        ],
        label='Pick your more preferred lottery between the two',
        widget=widgets.RadioSelect
    )
