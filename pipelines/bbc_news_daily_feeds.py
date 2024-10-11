"""
title: BBC News Daily Digest
description: This pipeline extract feeds and gives you a daily digest integrated with Fabric Patterns.
inspired and refactored from: @nathanwindisch (https://github.com/nathanwindisch)
author: Dario Palladino
author_url: https://github.com/dariopalladino
version: 0.1.0
license: MIT
TODO:
user message keyworkds based on the ArticleTypes to extract news from that category

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
		BBC_FEEDS_DOMAIN: str = Field(
			default=os.getenv("BBC_FEEDS_DOMAIN", "feeds.bbci.co.uk"),
			description="The OLLAMA model name"
		)
	

	def __init__(self):
		load_dotenv(find_dotenv(str(BASE_DIR / ".env")))
		self.DEBUG = os.getenv("DEBUG", False)
		self.name = "BBC News Daily Digest"
		self.llm: Ollama = None
		self.valves = self.Valves()
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


	def pipe(
		self, user_message: str, model_id: str, messages: List[dict], body: dict
	) -> Union[str, Generator, Iterator]:
		if self.DEBUG: print(f"pipe: {__name__}")
		if self.DEBUG: print(f"Body: {body}")
		if self.DEBUG: print(f"Temperature: {body.get('temperature', False)}")
		if self.DEBUG: print(f"UserMessage: {user_message}")
		if self.DEBUG: print(f"OLLAMA_HOST: {self.valves.OLLAMA_HOST}")
		if self.DEBUG: print(f"OLLAMA_MODEL_NAME: {self.valves.OLLAMA_MODEL_NAME}")

		self.fabric = Fabric(self.llm)
		self.fabric.set_user_message(user_message)
		self.fabric.find_pattern()

		if body.get('title', False):
			return self.__create_title()
		else:
			tools = BBCDailyDigest(fabric=self.fabric, bbc_domain=self.valves.BBC_FEEDS_DOMAIN)
			if self.fabric.get_pattern() in self.fabric.get_patterns():
				context = tools.get_bbc_news_content(user_message=user_message)
			else:
				context = tools.get_bbc_news_feed("top_stories")
			return context if context else "No information found"


	def __create_title(self):
		return 'BBC News digest'


class Fabric():
	# Define the allowlist of characters
	DEBUG = os.getenv("DEBUG", False)
	ALLOWLIST_PATTERN = re.compile(r"^[a-zA-Z0-9\s.,;:!?\-]+$")
	PATTERNS = {
        "languages": {
            "en": "English", 
            "it": "Italian"
        },
		"patterns": {
			'summarize': "summarize",
			'riassumi': "summarize",
		}
	}


	def __init__(self, llm: Ollama) -> None:
		self.system_pattern_message = ChatMessage(role="system")
		self.user_pattern_message = ChatMessage(role="user")
		self.user_message = None
		self.pattern = None
		self.llm = llm
		self.language = None
		

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
		for lang, text in self.get_available_languages().items():
			reg = fr'\b{re.escape(lang.lower())}\b'
			langfound = re.search(reg, self.user_message.lower())
			self.language = text if langfound else "English"

		if self.DEBUG: print(f"Language: {self.language}")

		for target, fn in self.PATTERNS["patterns"].items():
			reg = fr'\b{re.escape(target.lower())}\b'
			found = re.search(reg, self.user_message.lower())
			self.pattern = fn if found else self.pattern                    

		if self.DEBUG: print(f"Pattern: {self.pattern}")


	def apply_pattern(self, transcript: str, pattern: Optional[str] = None) -> str:
		"""
		Apply the pattern to return the assistant content

		Args:
			message (str): user message

		Returns:
			ChatResponse: response from llama-index Ollama
		"""
		self.pattern = pattern if pattern else self.pattern
		system_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/system.md"
		user_url = f"https://raw.githubusercontent.com/danielmiessler/fabric/main/patterns/{self.pattern}/user.md"

		# Fetch the prompt content
		system_content = self.__fetch_content_from_url(system_url)
		user_file_content = self.__fetch_content_from_url(user_url)

		self.system_pattern_message.content = system_content
		self.user_pattern_message.content = user_file_content + "\n" + transcript if user_file_content else transcript
		messages: List[ChatMessage] = [self.system_pattern_message, self.user_pattern_message]
		self.__call_ollama(messages)
		self.translate()
		return self.get_response_content()


	def apply_extra_pattern(self, prompt_template: PromptTemplate, message):
		message: ChatMessage = prompt_template.format_messages(input=message, llm=self.llm)
		self.__call_ollama(messages=message)
		self.translate()
		return self.get_response_content()


	def translate(self) -> None:
		if self.language != "English":
			self.__set_translation_prompt(self.language)
			self.__call_ollama([ChatMessage(role="system", content=self.translation_prompt), ChatMessage(role="user", content=self.get_response_content())])			
				

	def __set_translation_prompt(self, language: str):
		self.translation_prompt = f"""Translate the following text to {self.language}
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
   
    def _extract_url(self, text):
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



class BBCDailyDigest(Tools):
	# Regex to match a BBC News article URI.
	# Details:
	#  - Must use http or https.
	#  - Must be a bbc.com or bbc.co.uk domain.
	#  - Must be a news article or video.
	#  - Must have a valid ID (alphanumeric characters).
	URI_REGEX = re.compile("^(https?:\/\/)(www\.)?bbc\.(com|co\.uk)\/news\/(articles|videos)\/\w+$")

	class ArticleType(Enum):
		top_stories = "top_stories"
		world = "world"
		uk = "uk"
		business = "business"
		politics = "politics"
		health = "health"
		education = "education"
		science_and_environment = "science_and_environment"
		technology = "technology"
		entertainment_and_arts = "entertainment_and_arts"
		england = "england"
		northern_ireland = "northern_ireland"
		scotland = "scotland"
		wales = "wales"
		africa = "world/africa"
		asia = "world/asia"
		australia = "world/australia"
		europe = "world/europe"
		latin_america = "world/latin_america"
		middle_east = "world/middle_east"
		us_and_canada = "world/us_and_canada"
		def get_name(self) -> str: return self.name.replace("_", " ").title()
		def get_uri(self, domain) -> str: return f"https://{domain}/news/{self.value}/rss.xml" if self.name != "top_stories" else f"https://{domain}/news/rss.xml"

	def __init__(self, fabric: Fabric = None, bbc_domain: str = "feed.bbc.com" ):
		super().__init__()
		self.fabric = fabric
		self.bbc_domain = bbc_domain
		self.prompt: PromptTemplate = PromptTemplate(template="""You are a JSON format expert. Given an input array formatted with JSON, order the results by the "published" field descending to return a more readable list from the given input. Return only the most recent items, max 25, based on the "published" field, and don't add any of your comments.
Pay attention to the following fields available in each single row of the array: "title", "description", "link", "published" and provide a response using the following format:
Title: value of the "title" field
Description: value of the "description" field
Link: value of the "link" field
Published at: value of the "published" field

Input json array: {input}
""")
		self.DEBUG = os.getenv("DEBUG", False)
        
	def get_bbc_news_feed(
			self,
			type: ArticleType,
		) -> str:
		"""
		Get the latest news from the BBC, as an array of JSON objects with a title, description, link, and published date.
		:param type: The type of news to get. It can be any of the ArticleType enum values (world, uk, business, politics, health, education, science_and_environment, technology, entertainment_and_arts, england, northern_ireland, scotland, wales, world/africa, world/asia, world/australia, world/europe, world/latin_america, world/middle_east, world/us_and_canada).
		:return: A list of news items or an error message.
		"""
		type = self.ArticleType(type) # Enforce the type (it seems to get dropped by openwebui...)
		output = []
		try:
			response = requests.get(type.get_uri(self.bbc_domain))
			if not response.ok: 
				return f"Error: '{type}' ({type.get_uri(self.bbc_domain)}) not found ({response.status_code})"
			
			root = ElementTree.fromstring(response.content)
			for item in root.iter("item"): 
				output.append({
					"title": item.find("title").text,
					"description": item.find("description").text,
					"link": item.find("link").text,
					"published": item.find("pubDate").text,
				})
			
		except Exception as e:
			return f"Error: {e}"
		
		return self.fabric.apply_extra_pattern(self.prompt, json.dumps(output))

		# return json.dumps(output)
		

	def get_bbc_news_content(
		self,
		user_message: str,
	) -> str:
		"""
		Get the content of a news article from the BBC.
		:param uri: The URI of the article to get the content of, which should start with https://bbc.com/news or https://bbc.co.uk/news.
		:return: The content of the article or an error message.
		"""
		if user_message == "":
			return "Error: No User Message provided"
		
		url = super()._extract_url(user_message)

		if not re.match(self.URI_REGEX, url):
			return "Error: URI must be a BBC News article."

		content = ""
		try:
			response = requests.get(url)
			if not response.ok: return f"Error: '{url}' not found ({response.status_code})"
			article = BeautifulSoup(response.content, "html.parser").find("article")
			if article is None:
				return f"Error: Article content for {url} not found."
			
			paragraphs = article.find_all("p")
			for paragraph in paragraphs: content += f"{paragraph.text}\n"
		except Exception as e:
			return f"Error: {e}"

		if self.fabric.get_pattern():
			print(f"Inside the PATTERN: {self.fabric.get_pattern()}")
			return self.fabric.apply_pattern(content)
		
		return content
	