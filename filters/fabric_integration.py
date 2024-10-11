"""
title: Fabric Patterns Integration
description: This pipeline is a filter that integrates your queries with Fabric patterns so that you can use key words and get wonderful prompt applied automatically to get enhanced results
author: Dario Palladino
author_url: https://github.com/dariopalladino
version: 0.1.0
license: MIT
"""
import os
import re
import json
import requests
from enum import Enum
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ElementTree
from typing import Awaitable, Callable, Union, Generator, List, Iterator, Optional, Any
from pydantic import BaseModel, Field
from llama_index.core import ChatPromptTemplate, PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.core.schema import Document
from llama_index.core.llms import ChatMessage, ChatResponse

from utils.pipelines.main import get_last_user_message, get_last_assistant_message

BASE_DIR = Path(__file__).parent

class Pipeline:
    '''
    This pipeline extracts the transcript from a YouTube video and applies a Fabric pattern to it
    Be mindful that YouTube applies rate limit to the calls you make to its API
    '''
    class Valves(BaseModel):
        OLLAMA_HOST: str = Field(
            default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            description="The OLLAMA server"
        )
        OLLAMA_MODEL_NAME: str = Field(
            default=os.getenv("OLLAMA_MODEL_NAME", "llama3.1"),
            description="The OLLAMA model name"
        )


    def __init__(self):
        load_dotenv(find_dotenv(str(BASE_DIR / ".env")))
        self.type = "filter" # required to be understood by the pipelines server
        self.DEBUG = os.getenv("DEBUG", False)
        self.name = "Fabric Patterns integration filter"
        self.llm: Ollama = None
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Connect to all pipelines
            }
        )
        print(f"DEBUG: {self.DEBUG}")
        if self.DEBUG: self.set_llm() # Just for local tests


    async def on_startup(self):
        print(f"on_startup:{__name__}")
        self.set_llm()
        

    async def on_valves_updated(self):
        print(f"on_valves_updated:{__name__}")
        self.set_llm()


    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        self.llm = None


    def set_llm(self):
        self.llm = Ollama(
            model=self.valves.OLLAMA_MODEL_NAME, 
            base_url=self.valves.OLLAMA_HOST, 
            request_timeout=180.0, 
            context_window=30000,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        return self.llm


    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if self.DEBUG: print(f"pipe: {__name__}")
        if self.DEBUG: print(f"Body: {body}")
        if self.DEBUG: print(f"OLLAMA_HOST: {self.valves.OLLAMA_HOST}")
        if self.DEBUG: print(f"OLLAMA_MODEL_NAME: {self.valves.OLLAMA_MODEL_NAME}")

        messages = body["messages"]
        user_message = get_last_user_message(messages)
        print(f"User message: {user_message}")		

        self.fabric = Fabric(self.llm)
        self.fabric.set_user_message(user_message)
        self.fabric.find_pattern()

        if self.fabric.get_pattern() in self.fabric.get_patterns():
            filtered_user_message = self.fabric.apply_pattern()
            for message in reversed(messages):
                if message["role"] == "user":
                    message["content"] = filtered_user_message
                    break

        body = {**body, "messages": messages}
        return body


    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        """
        pass


    def __create_title(self):
        return 'BBC News digest'



class Fabric():
    # Define the allowlist of characters
    DEBUG = os.getenv("DEBUG", False)
    ALLOWLIST_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,;:!?\-]+$")
    PROMPTS = {
        'translate_to_english': """Translate the following text to English. Provide only the translated text and nothing else.
""",
        'translate_to_italian': """Translate the following text to Italian. Provide only the translated text and nothing else.
"""
    }
    PATTERNS = {
        "languages": {
            "en": "English", 
            "it": "Italian"
        },
        "patterns": {
            'summarize': "summarize",
            'riassumi': "summarize",
            'analyze': "analyze_presentation",
            'analizza': "analyze_presentation",
            'translate': PROMPTS['translate_to_english'],
            'traduci': PROMPTS['translate_to_italian']
        }
    }


    def __init__(self, llm: Ollama) -> None:
        self.system_pattern_message = ChatMessage(role="system")
        self.user_pattern_message = ChatMessage(role="user")
        self.user_message = None
        self.pattern = None
        self.llm = llm
        self.language = "en"
        self.__set_translation_prompt()


    def get_patterns(self) -> dict:
        return self.PATTERNS['patterns']


    def get_pattern(self):
        if self.DEBUG: print(f'Fabric Pattern: {self.pattern}')   
        return self.pattern if self.pattern else None


    def get_available_languages(self):
        return self.PATTERNS['languages']


    def get_response_content(self):
        if self.DEBUG: print(f'Ollama response: {self.response}')        
        return self.response.message.content if hasattr(self.response, 'message') else self.response


    def get_user_message(self):
        return self.user_message if self.user_message else None


    def set_user_message(self, user_message: str):
        self.user_message = user_message


    def find_pattern(self) -> None:
        """
        Check for the pattern to apply if any and set the pattern attribute
        """
        found = None
        self.pattern = None
        for lang in self.get_available_languages():
            reg = fr'\b{re.escape(lang.lower())}\b'
            langfound = re.search(reg, self.user_message.lower())
            self.language = lang.lower() if langfound else "en"

        if self.DEBUG: print(f"Language: {self.language}")

        for target, fn in self.get_patterns().items():
            reg = fr'\b{re.escape(target.lower())}\b'
            found = re.search(reg, self.user_message.lower())
            self.pattern = fn if found else self.pattern                    

        if self.DEBUG: print(f"Pattern: {self.pattern}")


    def apply_pattern(self, message: str = Optional[str], pattern: Optional[str] = Optional[str]) -> str:
        """
        Apply the pattern to return the assistant content

        Args:
            message (str): user message

        Returns:
            ChatResponse: response from llama-index Ollama
        """
        content = message if message else self.get_user_message()
        self.pattern = pattern if pattern else self.pattern
        if len(self.pattern) < 30:
            system_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/system.md"
            user_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/user.md"

            # Fetch the prompt content
            try:
                system_content = self.__fetch_content_from_url(system_url)
                user_file_content = self.__fetch_content_from_url(user_url)
            except Exception as e:
                if not self.pattern:
                    return f"Pattern not found in Fabric: {str(e)}"
        else:
            system_content = self.pattern

        self.system_pattern_message.content = system_content
        self.user_pattern_message.content = user_file_content + "\n" + content if user_file_content else content
        messages: List[ChatMessage] = [self.system_pattern_message, self.user_pattern_message]
        self.__call_ollama(messages)
        if self.language and self.language == "it":
            self.__call_ollama([ChatMessage(role="system", content=self.prompt), ChatMessage(role="user", content=self.get_response_content())])
        return self.get_response_content()


    def apply_extra_pattern(self, prompt_template: PromptTemplate, message):
        message: ChatMessage = prompt_template.format_messages(input=message, llm=self.llm)
        self.__call_ollama(messages=message)
        return self.get_response_content()
        

    def __set_translation_prompt(self):
        self.prompt = """Translate the following text to Italian
    """

    # Pull the URL content's from the GitHub repo
    def __fetch_content_from_url(self, url):
        """    Fetches content from the given URL.

        Args:
            url (str): The URL from which to fetch content.

        Returns:
            str: The sanitized content fetched from the URL.

        Raises:
            requests.RequestException: If an error occurs while making the request to the URL.
        """

        try:
            response = requests.get(url)
            response.raise_for_status()
            sanitized_content = self.__sanitize_content(response.text)
            return sanitized_content
        except requests.RequestException as e:
            return f"Error fetching Fabric Patterns: {str(e)}"
        

    # Sanitize the content, sort of. Prompt injection is the main threat so this isn't a huge deal
    def __sanitize_content(self, content):
        """    Sanitize the content by removing characters that do not match the ALLOWLIST_PATTERN.

        Args:
            content (str): The content to be sanitized.

        Returns:
            str: The sanitized content.
        """

        return "".join(char for char in content if self.ALLOWLIST_PATTERN.match(char))


    def __call_ollama(self, messages: List[ChatMessage]) -> None:
        ''' 
        Call OLLAMA API
        Args:
            messages (List[ChatMessage]): a List of ChatMessages with user message and system message

        Returns:
            str: the response content
        '''
        # Build the API call
        try:
            if self.DEBUG: print(f"Ollama Client: {self.llm}")
            self.response: ChatResponse = self.llm.chat(messages)
        except Exception as e:
            self.response = f"Error with the Ollama call in Fabric pattern workflow: {str(e)}"

