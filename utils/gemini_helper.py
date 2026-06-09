import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load default environment variables
load_dotenv()

class GeminiHelper:
    @staticmethod
    def configure(api_key: str = None) -> bool:
        """
        Configures the google-generativeai client.
        Uses the provided API key, or falls back to GEMINI_API_KEY from environment.
        Returns True if successful, False if no key was found.
        """
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            return False
        try:
            genai.configure(api_key=key)
            return True
        except Exception:
            return False

    @classmethod
    def _get_models_to_try(cls) -> list:
        """Helper to get a prioritized fallback list of available model names."""
        models_to_try = []
        try:
            available = [m.name for m in genai.list_models()]
            available_ids = [m.replace("models/", "") for m in available]
            
            # Prioritize stable release models with higher quotas, then previews
            preferences = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-3.5-flash",
                "gemini-1.5-flash"
            ]
            for p in preferences:
                if p in available_ids:
                    models_to_try.append(p)
            for a in available_ids:
                if "flash" in a and a not in models_to_try:
                    models_to_try.append(a)
        except Exception:
            pass
            
        if not models_to_try:
            models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        return models_to_try

    @classmethod
    def generate_with_fallback(cls, prompt: str, use_json: bool = False, system_instruction: str = None) -> str:
        """Attempts to generate content, falling back to other models if rate limits (429) or 404s occur."""
        models_to_try = cls._get_models_to_try()
        last_error = None
        
        for model_name in models_to_try:
            try:
                if use_json:
                    generation_config = {"response_mime_type": "application/json"}
                    model = genai.GenerativeModel(
                        model_name=model_name, 
                        generation_config=generation_config,
                        system_instruction=system_instruction
                    )
                else:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = e
                # Continue loop to try the next fallback model (e.g., if we hit 429 quota or 404)
                continue
                
        raise last_error if last_error else RuntimeError("Failed to generate content from any model.")

    @classmethod
    def _parse_json(cls, text: str):
        """Robustly parses JSON content from model output, stripping fences and extra text."""
        text = text.strip()
        
        # Clean markdown code fences if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Extract content between first and last bracket if standard loading fails
            first_bracket = text.find('[')
            last_bracket = text.rfind(']')
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            
            # Determine whether list or dict starts first
            is_list = False
            if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
                is_list = True
                
            if is_list and first_bracket != -1 and last_bracket != -1:
                json_str = text[first_bracket:last_bracket+1]
            elif first_brace != -1 and last_brace != -1:
                json_str = text[first_brace:last_brace+1]
            else:
                json_str = text
                
            return json.loads(json_str)

    @classmethod
    def explain_concept(cls, topic: str, api_key: str = None) -> dict:
        """
        Explains a topic in simple terms with analogies, key takeaways, and test questions.
        Returns a dictionary containing structured explanation components.
        """
        if not cls.configure(api_key):
            raise ValueError("Gemini API key is not configured. Please add it to your .env file or sidebar.")

        prompt = f"""
        Act as an expert, patient, and highly engaging educator. 
        Explain the topic: "{topic}".
        
        Provide a response that contains these distinct sections, written in clean markdown:
        1. **Simple Explanation**: A beginner-friendly breakdown of the concept using a relatable real-world analogy. Keep it engaging and simple.
        2. **Technical Details**: A deeper look into how it works under the hood for a student seeking high marks.
        3. **Key Takeaways**: A bulleted list of the most critical elements to remember.
        4. **Interview/Exam Prep**: 3 potential exam or interview questions about this topic, with concise model answers.
        
        Return your response ONLY in the following JSON format:
        {{
            "simple_explanation": "markdown text",
            "technical_details": "markdown text",
            "key_takeaways": ["point 1", "point 2", "point 3"],
            "exam_prep": [
                {{"question": "Q1", "answer": "A1"}},
                {{"question": "Q2", "answer": "A2"}},
                {{"question": "Q3", "answer": "A3"}}
            ]
        }}
        Do not wrap in any markdown formatting. Output raw JSON.
        """
        try:
            res_text = cls.generate_with_fallback(prompt, use_json=True)
            data = cls._parse_json(res_text)
            return data
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error parsing Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

    @classmethod
    def summarize_notes(cls, notes: str, api_key: str = None) -> dict:
        """
        Summarizes pasted notes or PDF content.
        Returns a summary dictionary.
        """
        if not cls.configure(api_key):
            raise ValueError("Gemini API key is not configured. Please add it to your .env file or sidebar.")

        prompt = f"""
        Analyze the following study notes and summarize them:
        ---
        {notes}
        ---
        
        Format your response into four parts and return it ONLY as a JSON object:
        1. **Executive Summary**: A concise paragraph summarizing the entire material (approx 150 words).
        2. **Key Concepts**: Bullet points highlighting the most important terms and concepts.
        3. **Exam Focus**: Critical formulas, facts, or definitions that are highly likely to appear on an exam.
        4. **Quick Revision Sheet**: A checklist of things a student should review right before entering an exam hall.
        
        JSON Schema:
        {{
            "summary": "markdown string",
            "key_concepts": ["concept 1", "concept 2"],
            "exam_focus": "markdown string",
            "revision_sheet": ["checkpoint 1", "checkpoint 2"]
        }}
        Do not wrap in markdown syntax. Return raw JSON.
        """
        try:
            res_text = cls.generate_with_fallback(prompt, use_json=True)
            data = cls._parse_json(res_text)
            return data
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

    @classmethod
    def generate_quiz(cls, topic: str, difficulty: str, api_key: str = None) -> list:
        """
        Generates 10 multiple-choice questions on a topic with a selected difficulty.
        Returns a list of questions, options, correct indices, and explanations.
        """
        if not cls.configure(api_key):
            raise ValueError("Gemini API key is not configured. Please add it to your .env file or sidebar.")

        prompt = f"""
        Generate exactly 10 multiple-choice questions about "{topic}" suited for a user at the "{difficulty}" level.
        
        For each question, provide:
        1. The question text.
        2. Exactly 4 options.
        3. The correct answer option index (0 for Option A, 1 for Option B, 2 for Option C, 3 for Option D).
        4. A detailed explanation of why the correct answer is right and why other options are incorrect.
        
        You must return the response as a JSON array of objects conforming to this schema:
        [
            {{
                "question": "...",
                "options": ["option A", "option B", "option C", "option D"],
                "correct_option_index": 0,
                "explanation": "..."
            }}
        ]
        Do not include markdown wrappers. Return raw JSON.
        """
        try:
            res_text = cls.generate_with_fallback(prompt, use_json=True)
            questions = cls._parse_json(res_text)
            if not isinstance(questions, list):
                raise ValueError("Expected a list of questions")
            return questions
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

    @classmethod
    def generate_flashcards(cls, topic: str, count: int = 8, api_key: str = None) -> list:
        """
        Generates a deck of flashcards based on a topic or snippet of notes.
        Returns a list of dicts with 'front' and 'back' fields.
        """
        if not cls.configure(api_key):
            raise ValueError("Gemini API key is not configured. Please add it to your .env file or sidebar.")

        prompt = f"""
        Generate exactly {count} flashcards for study purposes on the topic: "{topic}".
        Each flashcard should test a core term, formula, or concept.
        
        Return the result as a JSON array of objects conforming to this schema:
        [
            {{
                "front": "Term, question, or formula prompt",
                "back": "Short, clear answer, definition, or explanation (1-2 sentences)"
            }}
        ]
        Do not wrap in markdown syntax. Return raw JSON.
        """
        try:
            res_text = cls.generate_with_fallback(prompt, use_json=True)
            cards = cls._parse_json(res_text)
            if not isinstance(cards, list):
                raise ValueError("Expected a list of flashcards")
            return cards
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")

    @classmethod
    def chat_response(cls, message: str, chat_history: list, api_key: str = None):
        """
        Sends a message to the Gemini model in a multi-turn chat session.
        chat_history is a list of dicts: [{'role': 'user'|'model', 'text': '...'}]
        Returns the text response.
        """
        if not cls.configure(api_key):
            raise ValueError("Gemini API key is not configured. Please add it to your .env file or sidebar.")

        try:
            formatted_history = []
            for h in chat_history:
                formatted_history.append({
                    "role": "user" if h["role"] == "user" else "model",
                    "parts": [{"text": h["text"]}]
                })
            
            system_instruction = """
            You are 'Study Buddy', an intelligent, helpful, and friendly academic assistant. 
            You help students understand complex topics, debug code, review math proofs, 
            and explain study guides. Use markdown, tables, and short code snippets where appropriate. 
            Be concise and encouraging.
            """
            
            models_to_try = cls._get_models_to_try()
            last_error = None
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    chat = model.start_chat(history=formatted_history[:-1] if formatted_history else [])
                    response = chat.send_message(message)
                    return response.text
                except Exception as e:
                    last_error = e
                    continue
            raise last_error if last_error else RuntimeError("Chat generation failed.")
        except Exception as e:
            raise RuntimeError(f"Gemini API Error: {str(e)}")
            
    @classmethod
    def detect_difficulty_and_recommendations(cls, topic: str, api_key: str = None) -> dict:
        """
        Uses AI to detect the difficulty level of a topic and suggest 3 related follow-up study topics.
        """
        if not cls.configure(api_key):
            return {"difficulty": "Intermediate", "recommendations": []}
            
        prompt = f"""
        Analyze the study topic: "{topic}".
        Detect the academic difficulty of this topic (Beginner, Intermediate, or Advanced).
        Suggest exactly 3 related concepts or advanced topics that the student should study next.
        
        Return the response ONLY as a JSON object:
        {{
            "difficulty": "Beginner" | "Intermediate" | "Advanced",
            "explanation": "1-sentence explanation of why it is categorized this way",
            "recommendations": ["topic A", "topic B", "topic C"]
        }}
        Do not wrap in markdown block. Return raw JSON.
        """
        try:
            res_text = cls.generate_with_fallback(prompt, use_json=True)
            return cls._parse_json(res_text)
        except Exception:
            return {
                "difficulty": "Intermediate", 
                "explanation": "Default intermediate complexity",
                "recommendations": [f"{topic} advanced application", "Related systems", "Practical implementation"]
            }
