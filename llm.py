import os
from openai import OpenAI

from models import Session


class LLMClient:
    def __init__(self):
        # initialise the LLM client with the OpenAI API key
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def call(self, history):
        # call the LLM with the prompt

        response = self.client.responses.parse(
            model=self.model,
            # instructions=SYSTEM_PROMPT,
            input=history,
            text_format=Session,
        )

        return response.output[0].content[0].parsed
