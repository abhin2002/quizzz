from abc import abstractmethod

import openai
from bardapi import Bard
import json
from pydantic import BaseModel
from typing import List

class Option(BaseModel):
    option_name: str

class Question(BaseModel):
    question_name: str
    options: List[Option]
    correct_answer: str

class QuizResponse(BaseModel):
    questions: List[Question]

class QuizzPromptGenerator:
    @abstractmethod
    def generate_prompt():
        raise NotImplementedError


class MultipleChoicePromptGenerator(QuizzPromptGenerator):
    example = 'What is the capital of France?; A) Berlin; B) Rome; C) Paris (Correct); D) Amsterdam'

    @classmethod
    def generate_prompt(cls, content, num_quizzes, num_choices):
        require = (
            f'Give me {num_quizzes} multiple-choice questions'
            + f'each with {num_choices} possible answers'
            + " Clearly indicate the correct answer for each question."
            + " The questions should be based on the following reading passage:"
        )
        prompt = f'{require}\n{content}'
        return prompt


def get_quiz_prompt_generator(type) -> QuizzPromptGenerator:
    """
    Factory: This function returns a quiz prompt generator based on the type specified.

    Args:
      type: The type of quiz prompt generator to create.

    Returns:
      a QuizzPromptGenerator object based on the type parameter passed to it.
    """
    quiz_prompt_generators = {
        'multiple_choice': MultipleChoicePromptGenerator,
    }
    return quiz_prompt_generators[type]


class LLMService:
    @abstractmethod
    def call_service(key, prompt):
        raise NotImplementedError


class OpenAIGPT(LLMService):
    @staticmethod
    def call_service(key, prompt):
        openai.api_key = key
        print(prompt)
        response = openai.beta.chat.completions.parse(
            model='gpt-4o-mini-2024-07-18',
            messages=[
                {"role": "user", "content": prompt},
            ],
            response_format=QuizResponse,
        )
        
        response = response.choices[0].message.parsed.dict()  
        print("################",response)
        return response


class GoogleBard(LLMService):
    @staticmethod
    def call_service(key, prompt):
        bard = Bard(key)
        response = bard.get_answer(prompt)['content']
        return response


def get_llm_service(type) -> LLMService:
    """
    Factory: This function returns an instance of LLM service based on the type parameter passed to
    it.

    Args:
      type: The type of LLM service

    Returns:
      an instance of a LLM service class that use to call service.
    """
    llm_services = {
        'OpenAIGPT': OpenAIGPT,
        'GoogleBard': GoogleBard,
    }
    return llm_services[type]
