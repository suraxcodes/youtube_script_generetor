import os 
import requests
import json 
import streamlit as st 
from typing import List, Dict ,Optional
import time

##connection to my locally model ollama 
OLLAMA_API_URL = "http://127.0.0.1:11434/api"# port of my ollama 

MODEL_NAME = "llama3.2-vision"

#

class HTTPLocalLLM:
    """communicted with local llm model by HTTP API """

    def __init__(self, base_url = OLLAMA_API_URL, model_name = MODEL_NAME):
        self.base_url = base_url
        self.model_name = model_name
        self.generate_url = f"{base_url}/generate"#"http://127.0.0.1:11434/api/generate"
        self.chat_url = f"{base_url}/chat"#"http://127.0.0.1:11434/api/chat"

        #connection checking 
    def check_connection(self)->bool:
        """check if ollama is running  """
        try:
            response =  requests.get(f"{self.base_url}/tags",timeout=5)
            return response.status_code == 200 
        except:
            return print("not able to connect llm model ")
        
    def model_list(self)->list[str]:
        """list available models """
        try:
            response = requests.get(f"{self.base_url}/tags")
            if response.status_code == 200 :
                models = response.json().get("models",[])
                return [model["name"] for model in models ] 
            return[]
        except:
            return[]
        
    def generate_text(self, prompt: str, temperature:float = 0.7, max_tokens:int= 2000)->str :
        """Generate text using the local model"""
## in payload user input will send to my llm as a api request
        payload = {
            "model":self.model_name,
            "prompt":prompt,
            "stream":True,
            "options":{
                "temperature":temperature,
                "num_predict":max_tokens,
            }
        }
# my prompt will send to my base model if its get = 200  code then its whille recive output from my model and get it in json format 
        try :
            response = requests.post(self.generate_url,json=payload,timeout=120 )
            if response.status_code == 200:
                return response.json().get("response","")
            else :
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e :
            return f"Error while generating text :{e}"


## THIS FUnction will hwlp to remenber the past convo so based on that it will give me output

    def chat_completion(self, messages: list[dict], temperature: float = 0.7) -> str:
        """Chat completion using the local model"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error in chat: {str(e)}"

# research agent 
class HTTPResearchAgent:
    def __init__(self,llm: HTTPLocalLLM):
        self.llm = llm

    def researchAGent(self,topic :str)->str:
        """Research a topic using local model """
        researchAgent_prompt =f""" "Create a compelling and engaging script that covers the following aspects of {topic}. Write in a clear, conversational style suitable for YouTube narration. Use short, punchy sentences and include hooks that keep viewers interested. Structure the response with headings and bullet points for easy readability. Focus on storytelling and audience connection, not just dry facts. Cover:
- Key Facts & Statistics
- Present surprising or memorable numbers that grab attention.
- Highlight quick, digestible facts viewers can easily remember.
- Historical Context
- Explain the origins and evolution of the topic.
- Mention pivotal events or turning points that shaped its importance.
- Stories & Anecdotes
- Share fascinating human stories, myths, or quirky details.
- Include examples that make the topic relatable and entertaining.
- Current Relevance & Controversies
- Show why this topic matters today.
- Mention debates, trends, or hot takes that spark curiosity.
- Why It Matters to Viewers
- Connect the topic to everyday life, culture, or global impact.
- End with a thought‑provoking takeaway that encourages reflection or discussion."
"""
        return self.llm.generate_text(researchAgent_prompt, temperature=0.7)        
    
## script generator agent
class HTTPScriptGenerator:
    def __init__(self,llm:HTTPLocalLLM ):
        self.llm=llm
    
    def Script_generator(self,topic :str,researchAGent)->dict:
        """generete SCript in json format """
        Script_prompt = """
You are a professional YouTube scriptwriter with millions of subscribers.
Your task is to create engaging, well-structured YouTube scripts.
ALWAYS respond with valid JSON only — no extra commentary, explanations, or text outside the JSON.
"""
        user_prompt = f"""Create a YouTube script about: {topic}

Use the following research information to enrich the script:
{researchAGent}

Return a JSON object with exactly this structure:
{{
  "title": "Catchy, SEO-friendly YouTube title",
  "hook": "An attention-grabbing opening (first 15 seconds) that makes viewers stay",
  "introduction": "A short, conversational intro (around 30 seconds) explaining what viewers will learn",
  "segments": [
    {{
      "heading": "Segment 1 heading",
      "content": "Engaging content for segment 1. Include [PAUSE] markers and [VISUAL: description] cues for editing."
    }},
    {{
      "heading": "Segment 2 heading",
      "content": "Engaging content for segment 2 with natural speaking patterns."
    }},
    {{
      "heading": "Segment 3 heading",
      "content": "Engaging content for segment 3 with storytelling elements."
    }}
  ],
  "call_to_action": "A strong ending encouraging likes, subscribes, and comments",
  "video_length": "Estimated video length (e.g., '8-10 minutes')"
}}
Guidelines:
- Make the script conversational and easy to narrate.
- Use short, punchy sentences and natural speaking patterns.
- Add hooks, anecdotes, or surprising facts to keep viewers engaged.
- Ensure the JSON is valid and follows the exact structure above.
"""
        messages = [
            {"role": "system", "content": Script_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.llm.chat_completion(messages,temperature=0.8)
## trying to extract json from mdoel reponse 

        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != 0:
                jso_str = response[start:end]
                return json.load(jso_str)
            else :
                return self._create_fall_script(topic)
        except Exception as e:
            return self._create_fallback_script(topic)
        
    def _create_fallback_script(self, topic: str) -> dict:
        """Create a simple script if JSON parsing fails"""
        return {
            "title": f"Amazing Facts About {topic}",
            "hook": f"Did you know that {topic} has some incredible stories most people never hear about? Stick around to learn something amazing!",
            "introduction": f"In this video, we're exploring {topic}. We'll uncover fascinating facts, share surprising stories, and reveal why this matters more than you might think.",
            "segments": [
                {
                    "heading": f"The Story of {topic}",
                    "content": f"Let's start with the origins. {topic} has a rich history that's full of surprises... [PAUSE] [VISUAL: Show historical images or timeline]"
                },
                {
                    "heading": "Key Facts You Need to Know",
                    "content": "Here are the most important things to understand about this topic... [PAUSE] [VISUAL: Display key facts on screen]"
                },
                {
                    "heading": "Why This Matters Today",
                    "content": "You might wonder why this is relevant. Well, here are the reasons it's important right now... [PAUSE]"
                }
            ],
            "seo_keywords": [topic, f"{topic} explained", "youtube tutorial", "educational content", "learn online"],
            "call_to_action": "If you enjoyed this video and learned something new, please hit that like button and subscribe for more content like this! Leave a comment below with your thoughts.",
            "video_length": "8-10 minutes"
        }

class YouTubeScriptPipeline:
    def __init__(self, model_name=MODEL_NAME):
        self.llm = HTTPLocalLLM(model_name=MODEL_NAME)
        self.researcher = HTTPResearchAgent(self.llm)
        self.Script_generator = HTTPScriptGenerator(self.llm)

    def generate(self,topic:str)->dict:
        """generate a complete YOutube Script """

         # Step 1: Research the topic
        research = self.researcher.researchAGent(topic)

         # Step 2: Generate the script using research
        script = self.Script_generator.Script_generator(topic,research)

# Step 3: Return structured result
        return {
            "topic": topic,
            "research": research,
            "script": script
        }
    

def main():
    pipeline = YouTubeScriptPipeline()
    topic = "The History of the Internet"
    result = pipeline.generate(topic)

    print("=== YouTube Script Pipeline Output ===")
    print(f"Topic: {result['topic']}")
    print(f"Research: {result['research'][:200]}...")  # preview
    print(f"Script: {result['script'][:200]}...")      # preview


if __name__ == "__main__":
    main()
