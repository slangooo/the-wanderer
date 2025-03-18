#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

from src.llm_backend import MultimodalLlm, create_message, USER, ASSISTANT
from src.prompt_misc import *
from configs.config import WANDERER_IMG_PATH, ENTITY_IMG_PATH, ENV_IMG_PATH, FINAL_IMG_PATH
from src.log import logger
import re
from PIL import Image
from src.tools import remove_white_background, overlay_image


class TheWandererGame:
    def __init__(self):
        self.llm_model = MultimodalLlm()
        self.init_conv = [create_message(USER, init_pr), create_message()]
        self.prev_level_conv = []  # Conversation from previous level, useful for generating next level
        self.env_desc = ''  # Placeholder for the description of the current environment (area)
        self.level_conv = []  # Contains base conversation of the current level (game description + env description)
        self.talking_entity = ''  # Not used yet. To define other entities that talk to the wanderer
        self.helpful_entity = 'helpful bird'  # Main talking entity that is helping the wanderer
        self.exchange_conv = []  # Holds the entire conversation history of the current level

    def generate_env_desc(self):
        """ Called one time after initialization to generate the first level area.
         Otherwise, update_env_desc should be used.

         Returns:
            self.env_desc (str): The environment description.
        """
        env_conv = (self.init_conv[:-1] + [create_message(content="Provide the questions.")] +
                    [create_message(USER, env_pr), create_message()])
        self.env_desc = self.llm_model.generate_text(env_conv).replace("Assistant:", "").strip()
        self.level_conv = env_conv[:-1] + [create_message(content=self.env_desc)]
        self.generate_env_img()  # Update image
        return self.env_desc

    def update_env_desc(self):
        """ Called when the player decides to move, thus requiring a new area to be generated. The new area should
        logically reflect the progression of the game from the previous level.

        Returns:
            self.env_desc (str): Updated environment description.

        """

        # Save previous level conversation. It can be useful for future extensions.
        self.prev_level_conv = (list(self.level_conv) + [create_message(USER, self.get_conv_combined())])
        self.exchange_conv = []  # Clear the current level conversation history

        # Decide what is the logical next place that the wanderer reaches
        self.prev_level_conv[-1]['content'] += "After the wanderer's decision of movement, where should they reach?"
        env_conv = self.prev_level_conv + [create_message()]
        env_conv[-1]['content'] = self.llm_model.generate_text(env_conv).replace("Assistant:", "").strip()
        self.prev_level_conv = list(env_conv)
        env_desc = self.llm_model.generate_text(
            env_conv + [create_message(USER, 'Describe the new area that the wanderer reaches'), create_message()])
        logger.debug(env_desc)

        # To not complicate the image, we extract only 5 features of the new area.
        # If stronger models are used then next step can be skipped.
        env_desc_2 = self.llm_model.generate_text([create_message(USER, 'Describe the new area'),
                                                   create_message(content=env_desc),
                                                   create_message(USER,
                                                                  "Extract 5 important visual features in the new area."),
                                                   create_message()])

        #No mention of the wanderer is kept in the environment description. The game sounds more natural this way.
        self.env_desc = self.llm_model.generate_text([create_message(USER, "Rewrite the environment description in"
                                                                           " a single paragraph: \n"
                                                                     + env_desc_2.replace('wanderer', '').replace(
            'Wanderer', '').strip()), create_message()])

        self.level_conv = (self.init_conv[:-1] + [create_message(content="Provide the questions.")] +
                           [create_message(USER, env_pr), create_message(content=self.env_desc)])

        #Generate new environment image
        self.generate_env_img()

        return self.env_desc

    def generate_entity_exchange(self, helpful=True):
        """ Called one time after entering a new area to generate a helpful message by the helpful entity.

        Args:
            helpful (bool): Is it the helpful entity talking?

        Returns:
            entity_exchange (str): The response of the entity.
        """
        input_conv = self.level_conv + [create_message(USER, dialogue_single_exchange_gen_pr.format(
            self.helpful_entity if helpful else self.talking_entity)), create_message()]
        entity_exchange = self.llm_model.generate_text(input_conv).replace("Assistant:", "").replace('"', '').strip()
        # Update the current level chat history
        self.exchange_conv.append(dialogue_entity_response_pr.
                                  format(self.helpful_entity if helpful else self.talking_entity, entity_exchange))
        return entity_exchange

    def update_entity_exchange(self, helpful=True):
        """ Called every time the wanderer types an answer to the helpful entity which requires a further response
        by the entity. The new response is based on the entire conversation history of the current level.

        Args:
            helpful (bool): Is it the helpful entity talking?

        Returns:
            entity_exchange (str): The response of the entity.
        """
        input_conv = self.level_conv + [create_message(USER, dialogue_single_update_gen_pr.format(
            self.get_conv_combined(), self.helpful_entity if helpful else self.talking_entity)), create_message()]
        entity_exchange = (self.llm_model.generate_text(input_conv).
                           replace("Assistant:", "").replace('""', '"').
                           strip())
        logger.debug("The response is: " + entity_exchange)
        # Clean the response. Sometimes the LLM rewrites the entire conversation, or mentions the interlocutor twice.
        try:
            entity_exchange = re.findall(r'"([^"]+)"', entity_exchange)[-1].strip()  # To get last response
        except:
            logger.warning("Failed to parse the quoted text")

        logger.debug("The response after cleaning is: " + entity_exchange)
        # Update the current level chat history
        self.exchange_conv.append(dialogue_entity_response_pr.
                                  format(self.helpful_entity if helpful else self.talking_entity, entity_exchange))
        return entity_exchange

    def wanderer_input(self, p_input):
        """ Handle user input. The wanderer either continues the dialogue with the other talking entity, or moves to
        a new area. This is determined by understanding whether any movement was implied in the input or not. If the
        wanderer is moving, a new area and level are generated.

        Args:
            p_input (str): The last input from the user.

        Returns:
            new_env_desc (Optional[str]): The new environment description if movement triggered
                                            a new environment; otherwise, None.
            entity_exchange (str): A statement told by the entity to the wanderer.

        """
        logger.debug("User inputted: " + str(p_input))

        # Update current chat history
        self.exchange_conv.append(dialogue_wanderer_response_pr.format(p_input))

        # Analyze whether any movement was implied by the user
        result = self.llm_model.generate_text(
            [create_message(USER, wanderer_input_decision_pr.format(self.exchange_conv[-1])),
             create_message(ASSISTANT)])
        result = self.llm_model.generate_text(
            [create_message(USER, f"If the following text confirm movement, answer '2', else answer '1'. \n {result}"),
             create_message(ASSISTANT)])

        logger.debug("Analyzing input: '{}'. ".format(p_input) + ' Result: {} -> '.format(
            result) + ('Dialogue' if '1' in result else 'Movement'))

        if '2' not in result:  # Continue dialogue
            return None, self.update_entity_exchange()
        else:  # Stop dialogue and change environment
            return self.update_env_desc(), self.generate_entity_exchange(True)

    def generate_env_img(self):
        """ After reaching a new area, a new image is generated. The character image is also overlayed on top of the
        new area. """
        #This next step summarizes the description. It enhances the final image result
        summarized = self.llm_model.generate_text([create_message(USER,
                                          "Summarize in a single paragraph the area described by: \n" + self.env_desc),
                                                   create_message()])
        description = 'Draw the area: ' + summarized
        logger.debug("Generating env image with the following description: " + description)
        self.llm_model.generate_image(description, file_path=ENV_IMG_PATH)

        background = overlay_image(ENV_IMG_PATH, WANDERER_IMG_PATH, (-20, 150), (300, 300))
        background.save(FINAL_IMG_PATH, format='PNG')

    def generate_wanderer_img(self, wanderer_desc_pr=default_wanderer_pr):
        """
        Generates an image of the Wanderer character based on a given description.
        It can be used to update the Wanderer’s image dynamically during the game.

        Args:
            wanderer_desc_prompt (str): The textual description used to generate the image.

        Returns:
            None
        """
        description = wanderer_desc_pr + character_white_bkg_pr
        self.llm_model.generate_image(description, file_path=WANDERER_IMG_PATH)

    def generate_talking_entity_img(self, entity_desc_pr="Generate an image of a helpful talking bird"):
        description = entity_desc_pr + character_white_bkg_pr
        self.llm_model.generate_image(description=description, file_path=ENTITY_IMG_PATH)

    def get_conv_combined(self):
        return ' '.join(self.exchange_conv) + ' '


if __name__ == '__main__':
    game_ctrl = TheWandererGame()
    # game_ctrl.generate_wanderer_img()
    print(game_ctrl.generate_env_desc())
    # game_ctrl.generate_env_img()
    print(game_ctrl.generate_entity_exchange())
    while 1:
        game_ctrl.wanderer_input(input())
