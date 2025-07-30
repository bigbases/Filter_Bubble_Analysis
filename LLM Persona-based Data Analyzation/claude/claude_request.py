"""
Claude API Client Module

This module provides a client interface for interacting with the Anthropic Claude API.
It handles message management, response validation, and retry logic for robust operation.

Author: Research Team
Date: 2024
"""

import anthropic
import re
import time
import json
import random


class Claude:
    """
    Claude API client for structured political bias analysis.
    
    This class manages interactions with the Anthropic Claude API, including
    message threading, response validation, and retry mechanisms.
    """

    def __init__(self, model_version):
        """
        Initialize Claude client.
        
        Args:
            model_version (str): The Claude model version to use (e.g., 'claude-3-5-sonnet-20241022')
        """
        self.API_KEY = ''  # API key should be set via environment variable
        self.model = model_version
        self.messages = []
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def add_role(self, role):
        """
        Add a system role for the conversation.
        
        Args:
            role (str): The system role prompt to set
        """
        self.role = role

    def add_message(self, role, content):
        """
        Add a message to the conversation thread.
        
        Args:
            role (str): The role of the message sender ('user' or 'assistant')
            content (str): The message content
        """
        self.messages.append({"role": role, "content": content})

    def check_answer(self, answer):
        """
        Validate and extract JSON response from Claude answer.
        
        This method uses regex patterns to extract structured JSON responses
        containing political analysis data.
        
        Args:
            answer (str): The raw response from Claude
            
        Returns:
            str or None: Extracted JSON string if valid, None otherwise
        """
        # First attempt: Match JSON that includes "Reasoning"
        match = re.search(r'({.*"Political":.*?"Reasoning":.*?})', answer, re.DOTALL)
        
        if match:
            json_part = match.group(1)  # Extract the JSON part including "Reasoning"
        else:
            # Second attempt: Match JSON that includes up to the second closing brace after "Bias"
            match = re.search(r'({.*"Political":.*?"Bias":.*?}\s*})', answer, re.DOTALL)
            if match:
                json_part = match.group(1)  # Extract the JSON part up to the second closing brace
            else:
                json_part = None  # Return None if no match is found
        
        return json_part

    def run(self, prompt):
        """
        Execute a prompt and get a validated response.
        
        This method handles the complete request-response cycle including
        retries for failed attempts and response validation.
        
        Args:
            prompt (str): The user prompt to send to Claude
            
        Returns:
            str or None: Validated JSON response or None if all attempts failed
        """
        self.add_message("user", prompt)

        for attempt in range(self.max_retries):
            try:
                self.client = anthropic.Anthropic(api_key=self.API_KEY)

                completion = self.client.messages.create(
                    model=self.model,
                    system=self.role,
                    max_tokens=4096,
                    temperature=0.2,
                    messages=self.messages
                )
                
                answer = completion.content[0].text
                
                # Convert the completion object to a dictionary and print it as JSON
                completion_dict = completion.to_dict()
                completion_json = json.dumps(completion_dict, indent=4)
                print(f"Completion in JSON format (Attempt {attempt + 1}):")

                checked_answer = self.check_answer(answer)
                if checked_answer:
                    self.add_message("assistant", answer)
                    return checked_answer
                else:
                    print(f"Attempt {attempt + 1}: Invalid response format. Retrying...")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                time.sleep(60)

        print("Max retries reached. Unable to get a valid answer.")
        return None