#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.


"""Narrative Generation Prompts"""

init_pr = (
    "I need help in designing The Wanderer game levels. It is a single-player game where the "
    "player controls a traveler exploring foreign lands. The Wanderer must escape harm, overcome challenges, "
    "and progress through different environments. At each level of the journey, I will ask for describing "
    "some aspect of the game.")

env_pr = (
    "Describe the visual aspects of the area: \n "
    " 1. What is the place? For example, a forest, a village, a city, a cave, etc.\n "
    " 2. Describe up to four qualities of the surrounding objects (For example, tall trees, green buildings, dirty water, etc.)\n "
    " 3. Describe up to two objects that might be dangerous, mysterious, or useful.\n "
    " 4. Describe up to two other entities (humans or creatures) and what they are doing.\n "
    " Provide a single concise paragraph describing these aspects.")

dialogue_single_exchange_gen_pr = ('Generate a unique sentence that the {} speaks to '
                                   'the wanderer. The answer should only '
                                   'include the sentence enclosed in quotes "". It should be one sentence describing '
                                   'new information not mentioned before. ')

dialogue_single_update_gen_pr = (' {} '
                                 ' Continue the conversation by generating a unique answer by the {} to the wanderer.'
                                 ' Your answer should include the new short sentence which provides unique and novel'
                                 ' information, not mentioned before.')

dialogue_wanderer_response_pr = 'The wanderer said: "{}."'

dialogue_entity_response_gen_pr = ("Generate a response by {} to the wanderer's final answer. The response should be an"
                                   " acknowledgement only, with no further questions.")

dialogue_entity_response_pr = 'The {} said: "{}"'

wanderer_input_decision_pr = ('{}. Analyze what the wanderer said and decide if they are moving or intending to move.'
                              ' I explain what movement means below. '
                              'A movement is implied by looking for something, fighting something, going somewhere, '
                              'taking a path, jumping, climbing, and similar verbs. Otherwise, not moving is '
                              'implied by asking questions, making remarks, greetings, or verbs like thinking, loving, '
                              'reading, and other similar actions. '
                              'Is there any intention of moving?')


update_env_pr = ('According to the wanderer movement, create a new area different than the first one. \n '
                 + env_pr)

"""Image Generation Prompts"""
character_white_bkg_pr = (' Only the character body should be visible floating in air, with no background'
                          ' (transparent background if possible) or a plain white background for easy editing.')
default_wanderer_pr = 'Generate a character of a wandering traveler.'
