#  Copyright (c) 2025. Salim Janji. All rights reserved.
#  Unauthorized copying, distribution, or modification of this file is strictly prohibited.

from PIL import Image
import torch
from transformers import AutoModelForCausalLM
from models.janus.models import MultiModalityCausalLM, VLChatProcessor
import random
import os
import numpy as np
from pathlib import Path
from src.log import logger
from configs.config import BASE_DIR, MODEL_PATH, TEXT_GEN_MAX_TOKENS, CFG_WEIGHT_IMG, FINAL_IMG_PATH, MODEL_NAME
from huggingface_hub import snapshot_download

USER = '<|User|>'
ASSISTANT = '<|Assistant|>'


def create_message(role: str = ASSISTANT, content: str = "") -> dict:
    return {"role": role, "content": content}


class MultimodalLlm:
    def __init__(self, model_path=MODEL_PATH):
        if model_path.exists() and any(model_path.iterdir()) and (model_path/'preprocessor_config.json').exists():
            logger.info("Model files found")
        else:
            logger.info("Model files not found. Downloading..")
            model_path.mkdir(parents=True, exist_ok=True)
            snapshot_download(repo_id=MODEL_NAME, local_dir=str(model_path), local_dir_use_symlinks=False)

        self.vl_chat_processor: VLChatProcessor = VLChatProcessor.from_pretrained(model_path)
        self.tokenizer = self.vl_chat_processor.tokenizer

        self.vl_gpt: MultiModalityCausalLM = AutoModelForCausalLM.from_pretrained(
            model_path, trust_remote_code=True
        )
        self.vl_gpt = self.vl_gpt.to(torch.bfloat16).cuda().eval()

    def generate_text(self, conversation):
        #The different way of generating embeddings bellow was found to generate better results than the commented one.
        sft_format = self.vl_chat_processor.apply_sft_template_for_multi_turn_prompts(
            conversations=conversation,
            sft_format=self.vl_chat_processor.sft_format,
            system_prompt="",
        )

        # Encode the text
        input_ids = self.vl_chat_processor.tokenizer.encode(sft_format, return_tensors="pt").to(self.vl_gpt.device)

        # Ensure batch dimension is present
        if len(input_ids.shape) == 1:
            input_ids = input_ids.unsqueeze(0)  # Shape: [1, seq_len]

        # Create attention mask (all ones, assuming no padding)
        attention_mask = torch.ones_like(input_ids).to(self.vl_gpt.device)

        # Convert input_ids to embeddings
        inputs_embeds = self.vl_gpt.language_model.get_input_embeddings()(input_ids)

        outputs = self.vl_gpt.language_model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,  # Pass the mask explicitly
            pad_token_id=self.tokenizer.eos_token_id,
            bos_token_id=self.tokenizer.bos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            max_new_tokens=TEXT_GEN_MAX_TOKENS,
            do_sample=False,
            use_cache=False,
        )

        # prepare_inputs = self.vl_chat_processor(
        #     conversations=conversation,
        #     images = [],
        #     force_batchify=True
        # ).to(self.vl_gpt.device)
        #
        # inputs_embeds = self.vl_gpt.prepare_inputs_embeds(**prepare_inputs)
        #
        # outputs = self.vl_gpt.language_model.generate(
        #     inputs_embeds=inputs_embeds,
        #     attention_mask=prepare_inputs.attention_mask,
        #     pad_token_id=self.tokenizer.eos_token_id,
        #     bos_token_id=self.tokenizer.bos_token_id,
        #     eos_token_id=self.tokenizer.eos_token_id,
        #     max_new_tokens=TEXT_GEN_MAX_TOKENS,
        #     do_sample=True,
        #     temperature=0.005,
        #     use_cache=False,
        # )

        answer = self.tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
        return answer

    @torch.inference_mode()
    def generate_image(self,
                       description: str,
                       temperature: float = 0.00001,
                       parallel_size: int = 1,
                       cfg_weight: float = CFG_WEIGHT_IMG,
                       image_token_num_per_image: int = 576,
                       img_size: int = 384,
                       patch_size: int = 16,
                       file_path: Path = BASE_DIR / 'images' / 'img.jpg'):
        conversation = [
            {
                "role": USER,
                "content": description,
            },
            {"role": "<|Assistant|>", "content": ""},
        ]

        prompt = self.vl_chat_processor.apply_sft_template_for_multi_turn_prompts(
            conversations=conversation,
            sft_format=self.vl_chat_processor.sft_format,
            system_prompt="",
        ) + self.vl_chat_processor.image_start_tag

        input_ids = self.vl_chat_processor.tokenizer.encode(prompt)
        input_ids = torch.LongTensor(input_ids)

        tokens = torch.zeros((parallel_size * 2, len(input_ids)), dtype=torch.int).cuda()
        for i in range(parallel_size * 2):
            tokens[i, :] = input_ids
            if i % 2 != 0:
                tokens[i, 1:-1] = self.vl_chat_processor.pad_id

        inputs_embeds = self.vl_gpt.language_model.get_input_embeddings()(tokens)

        generated_tokens = torch.zeros((parallel_size, image_token_num_per_image), dtype=torch.int).cuda()

        for i in range(image_token_num_per_image):
            outputs = self.vl_gpt.language_model.model(inputs_embeds=inputs_embeds, use_cache=True,
                                                       past_key_values=outputs.past_key_values if i != 0 else None)
            hidden_states = outputs.last_hidden_state

            logits = self.vl_gpt.gen_head(hidden_states[:, -1, :])
            logit_cond = logits[0::2, :]
            logit_uncond = logits[1::2, :]

            logits = logit_uncond + cfg_weight * (logit_cond - logit_uncond)
            probs = torch.softmax(logits / temperature, dim=-1)

            next_token = torch.multinomial(probs, num_samples=1)
            generated_tokens[:, i] = next_token.squeeze(dim=-1)

            next_token = torch.cat([next_token.unsqueeze(dim=1), next_token.unsqueeze(dim=1)], dim=1).view(-1)
            img_embeds = self.vl_gpt.prepare_gen_img_embeds(next_token)
            inputs_embeds = img_embeds.unsqueeze(dim=1)

        dec = self.vl_gpt.gen_vision_model.decode_code(generated_tokens.to(dtype=torch.int),
                                                       shape=[parallel_size, 8, img_size // patch_size,
                                                              img_size // patch_size])
        dec = dec.to(torch.float32).cpu().numpy().transpose(0, 2, 3, 1)

        dec = np.clip((dec + 1) / 2 * 255, 0, 255)

        visual_img = np.zeros((parallel_size, img_size, img_size, 3), dtype=np.uint8)
        visual_img[:, :, :] = dec

        os.makedirs(file_path.parent, exist_ok=True)
        Image.fromarray(visual_img[0]).save(file_path)

