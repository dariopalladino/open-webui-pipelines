"""
title: Youtube Transcript Pipeline
description: A pipeline fully integrated with Fabric Patterns that returns the full, detailed youtube transcript summarizations in English or Italian of a passed in youtube url.
Inspired by: a work from Ekatiyar (https://github.com/ekatiyar)
author: Dario Palladino
author_url: https://github.com/dariopalladino
version: 0.1.0
license: MIT
"""
import os
import re
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Union, Generator, Iterator
from llama_index.llms.ollama import Ollama
from llama_index.core.schema import Document
from llama_index.core.llms import ChatMessage, ChatResponse
from llama_index.readers.youtube_transcript import YoutubeTranscriptReader
from llama_index.readers.youtube_transcript.utils import is_youtube_video


class Pipeline:
    '''
    This pipeline extracts the transcript from a YouTube video and applies a Fabric pattern to it
    Be mindful that YouTube applies rate limit to the calls you make to its API
    '''
    class Valves(BaseModel):
        OLLAMA_HOST: str
        OLLAMA_MODEL_NAME: str
        YOUTUBE_API_KEY: str
        

    def __init__(self):
        load_dotenv()
        self.DEBUG = os.getenv("DEBUG", False)
        self.name = "Youtube Transcript Generation Pipeline"
        self.llm: Ollama = None
        self.valves = self.Valves(
            **{
                "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                "OLLAMA_MODEL_NAME": os.getenv("OLLAMA_MODEL_NAME", "llama3"),
                "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY", ""),
            }
        )         
        print(f"DEBUG: {self.DEBUG}")
        if self.DEBUG: self.set_llm() # Just for local tests
        print(f"OLLAMA_HOST: {self.valves.OLLAMA_HOST}")
        print(f"OLLAMA_MODEL_NAME: {self.valves.OLLAMA_MODEL_NAME}")

    async def on_startup(self):
        print(f"on_startup:{__name__}")
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
            temperature=0.0,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        return self.llm
    

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        if self.DEBUG: print(f"pipe: {__name__}")
        if self.DEBUG: print(f"Body: {body}")
        if self.DEBUG: print(f"Temperature: {body.get('temperature', False)}")
        if self.DEBUG: print(f"UserMessage: {user_message}")
        
        self.fabric = Fabric(self.llm)
        self.fabric.set_user_message(user_message)
        self.fabric.find_pattern()

        if body.get('temperature'):
            tools = YouTubeTool(self.fabric)
            context = tools.get_youtube_transcript()
            return context if context else "No information found"
        else:
            return self.__create_title()


    def __create_title(self):
        return 'Youtube Transcript'


class Fabric():
    # Define the allowlist of characters
    DEBUG = os.getenv("DEBUG", False)
    ALLOWLIST_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,;:!?\-]+$")
    PATTERNS = {
        "languages": ["en", "it"],
        "patterns": {
            'extract wisdom':  "extract_wisdom",
            'summarize': "summarize",
            'estrai saggezza': "extract_wisdom",
            'riassumi': "summarize",
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


    def get_pattern(self):
        if self.DEBUG: print(f'Fabric Pattern: {self.pattern}')   
        return self.pattern if self.pattern else None


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
        for lang in self.PATTERNS["languages"]:
            reg = fr'\b{re.escape(lang.lower())}\b'
            langfound = re.search(reg, self.user_message)
            self.language = lang.lower() if langfound else "en"

        if self.DEBUG: print(f"Language: {self.language}")

        for target, fn in self.PATTERNS["patterns"].items():
            reg = fr'\b{re.escape(target.lower())}\b'
            found = re.search(reg, self.user_message)
            self.pattern = fn if found else self.pattern                    

        if self.DEBUG: print(f"Pattern: {self.pattern}")


    def apply_pattern(self, transcript: str) -> str:
        """
        Apply the pattern to return the assistant content

        Args:
            message (str): user message

        Returns:
            ChatResponse: response from llama-index Ollama
        """
        system_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/system.md"
        user_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/user.md"

        # Fetch the prompt content
        system_content = self.__fetch_content_from_url(system_url)
        user_file_content = self.__fetch_content_from_url(user_url)

        self.system_pattern_message.content = system_content
        self.user_pattern_message.content = user_file_content + "\n" + transcript
        messages: List[ChatMessage] = [self.system_pattern_message, self.user_pattern_message]
        self.__call_ollama(messages)        
        if self.language and self.language == "it":
            self.__call_ollama([ChatMessage(role="system", content=self.prompt), ChatMessage(role="user", content=self.get_response_content())])
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


class Tools():
    def __init__(self):
        self.citation = True


class YouTubeTool(Tools):
    def __init__(self, fabric: Fabric = None):        
        super().__init__()
        self.fabric = fabric
        self.url = self.__extract_url(self.fabric.get_user_message())
        self.DEBUG = os.getenv("DEBUG", False)


    def get_youtube_transcript(self) -> str:
        """
        Provides the title and full transcript of a YouTube video in English.
        Only use if the user supplied a valid YouTube URL.
        Examples of valid YouTube URLs: https://youtu.be/dQw4w9WgXcQ, https://www.youtube.com/watch?v=dQw4w9WgXcQ

        :return: The title and full transcript of the YouTube video in English, or an error message.
        """

        try:
            error_message = f"Error: Invalid YouTube URL: {self.url}"
            if not self.url or self.url == "":
                return error_message

            print(f'URL: {self.url}')

            if type(self.url) == str and is_youtube_video(self.url):
                loader = YoutubeTranscriptReader()
                print(f'Youtube Loader: {loader}')
                if self.DEBUG and os.getenv("TEST_TEXT"): 
                    transcript = [Document(id_='-IAwW3pUEew', embedding=None, metadata={'video_id': '-IAwW3pUEew'}, excluded_embed_metadata_keys=[], excluded_llm_metadata_keys=[], relationships={}, text=os.getenv("TEST_TEXT"), mimetype='text/plain', start_char_idx=None, end_char_idx=None, text_template='{metadata_str}\n\n{content}', metadata_template='{key}: {value}', metadata_seperator='\n')]
                else:
                    transcript = loader.load_data(
                        ytlinks=[self.url]
                    )
                print(f'Youtube Transcript: {transcript}')
                
                if len(transcript) == 0:
                    error_message = f"Error: Failed to find transcript for {self.url}"
                    return error_message
            else:
                error_message = f"Error: This '{self.url}' is not a Youtube video url"
                return error_message
                
            # title = transcript[0].metadata["video_id"]
            transcript = " ".join([document.text.replace('\n', ' ') for document in transcript])
            
            if self.fabric.get_pattern():
                print(f"Inside the PATTERN: {self.fabric.get_pattern()}")                
                return self.fabric.apply_pattern(transcript)
            return transcript

        except Exception as e:
            error_message = f"Error: {str(e)}"
            return error_message
   

    def __extract_url(self, text):
        """
        Extracts URL(s) from the given text.
        
        Args:
            text (str): The input string containing one or more URLs.
        
        Returns:
            list: A list of extracted URLs.
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        
        urls = re.findall(url_pattern, text)
        
        return urls[0] if len(urls) > 0 else urls
