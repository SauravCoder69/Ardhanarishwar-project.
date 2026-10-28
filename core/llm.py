import requests
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
from typing import List, Optional

class OllamaLLM:
    """Wrapper for locally hosted open-source LLM via Ollama API."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_DEFAULT_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def check_availability(self) -> bool:
        """Check if Ollama service is reachable on localhost."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def list_available_models(self) -> List[str]:
        """Fetch list of pulled models in Ollama."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                return [m['name'] for m in data.get('models', [])]
        except Exception:
            pass
        return [self.model]

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, timeout: int = 90) -> str:
        """
        Generate completion using local Ollama model.
        Auto-detects active pulled model or returns intelligent fallback response if model is missing.
        """
        if not self.check_availability():
            return self._fallback_response(prompt, system_prompt)

        # Auto-detect available pulled models if default model is not listed
        available_models = self.list_available_models()
        active_model = self.model
        if available_models and active_model not in available_models and active_model + ":latest" not in available_models:
            active_model = available_models[0]

        payload = {
            "model": active_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            elif response.status_code == 404:
                return self._fallback_response(
                    prompt, system_prompt,
                    f"Model '{active_model}' is not pulled in Ollama yet. Run `ollama pull {active_model}` in your terminal."
                )
            else:
                return f"⚠️ Ollama returned HTTP error {response.status_code}. Ensure model '{active_model}' is pulled using `ollama pull {active_model}`."
        except Exception as e:
            return self._fallback_response(prompt, system_prompt, str(e))

    def _fallback_response(self, user_prompt: str, system_prompt: Optional[str] = None, err_msg: str = "") -> str:
        """
        Intelligent local fallback generator if Ollama is not active locally.
        Provides realistic, structured assistance while indicating local Ollama status.
        """
        prompt_lower = user_prompt.lower()
        system_lower = (system_prompt or "").lower()

        # Handle Intent Classification prompt fallback specifically
        if "intent classification" in system_lower or "available agents" in system_lower:
            if any(k in prompt_lower for k in ["interview", "mock", "behavioral"]):
                return "Interview Agent"
            elif any(k in prompt_lower for k in ["resume", "resumes", "cv", "ats", "bullet point", "portfolio"]):
                return "Resume Agent"
            elif any(k in prompt_lower for k in ["career", "roadmap", "learning", "skill", "skills", "job", "java", "python", "coding", "learn", "growth"]):
                return "Career Agent"
            else:
                return "General Assistant"
        
        fallback_notice = (
            "\n\n*💡 Note: Ollama is currently disconnected or loading on `http://localhost:11434`. "
            "To enable live open-source LLM generation, run `ollama serve` and `ollama pull llama3.2` on your system.*"
        )
        if "career counsellor" in system_lower or "career counselling" in prompt_lower:
            return (
                "### 🎓 Career Counselling Guidance\n"
                "**College or course choice**\n"
                "- Compare accreditation, curriculum, faculty, practical projects, internship access, total fees, and verified placement reports.\n"
                "- Shortlist 3 options: one ambitious, one realistic, and one affordable option.\n"
                "- Verify eligibility, entrance exams, scholarships, and fees on the official college or exam website.\n\n"
                "**Private-sector options**\n"
                "For technology interests, build programming fundamentals, projects, a portfolio, and interview skills. Suitable entry paths include software development, data, testing, cloud, and support engineering.\n\n"
                "**Government-sector options**\n"
                "Research the exact eligibility and syllabus for exams such as SSC, banking, state public service, railways, or technical recruitment. Start with one target exam and follow its official notification.\n\n"
                "**Next 30 days**\n"
                "1. Compare three colleges or courses using the checklist above.\n"
                "2. Select one private and one government career path to investigate.\n"
                "3. Check official eligibility and exam dates.\n"
                "4. Complete one practical project or foundational study plan."
                + fallback_notice
            )
        elif "career" in prompt_lower or "roadmap" in prompt_lower or "learn" in prompt_lower or "ai engineer" in prompt_lower:
            return (
                "### 🎯 Recommended Career Roadmap for AI Engineering\n"
                "1. **Core Programming**: Master Python 3.11+, OOP, AsyncIO, and Typing.\n"
                "2. **Data & ML Foundations**: NumPy, Pandas, Scikit-learn, and PyTorch.\n"
                "3. **Backend & APIs**: REST APIs, databases, and reliable data handling.\n"
                "4. **Local LLM Integration**: Ollama and HuggingFace Transformers.\n"
                "5. **Production Skills**: FastAPI, Docker, Async Queues, and Monitoring.\n\n"
                "**Recommended Action**: Build an end-to-end AI application with a tested API."
                + fallback_notice
            )
        elif "interview" in prompt_lower or "question" in prompt_lower:
            return (
                "### 🎤 Technical Interview Question\n"
                "**Question**: Explain how you would design and test a reliable REST API for a production application.\n\n"
                "**Key points to touch upon**:\n"
                "- Clear request and response schemas\n"
                "- Input validation, error handling, and authentication\n"
                "- Automated tests, observability, and performance"
                + fallback_notice
            )
        else:
            return (
                f"### 🤖 Ardhanarishwar AI Assistant\n"
                f"Thank you for your question: *\"{user_prompt[:80]}\"*\n\n"
                f"I can assist with career planning, resume analysis, skill development, and interview preparation.\n"
                + fallback_notice
            )

# Global LLM instance
llm_client = OllamaLLM()
