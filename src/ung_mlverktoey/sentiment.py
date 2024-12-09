from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables.base import Runnable

from ung_mlverktoey.prompts import SENTIMENT_ANALYSE



class SentimentModel:

    
    def __init__(self) -> None:
        self.llama_model = ChatOllama(model = "llama3.2", temperature = 0)


    def create_prompt(self, prompt_template: str) -> PromptTemplate:
        return PromptTemplate.from_template(prompt_template)


    def create_ollama_chain(self, ollama_llm: ChatOllama, 
                            prompt_template: PromptTemplate) -> Runnable:
        return prompt_template | ollama_llm | JsonOutputParser()
    
    def run_model(self, text):

        sentiment_prompt = self.create_prompt(SENTIMENT_ANALYSE)

        model = self.create_ollama_chain(self.llama_model,
                                         sentiment_prompt)

        text = text

        inp = {'text': text}

        output = model.invoke(inp)

        sentiment = output.get('sentiment', 'Model failed')

        final_output = {
            'text': text,
            'sentiment': sentiment
        }

        return final_output

if __name__ == '__main__':
    pass