import requests
import json
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
from typing import Dict, Any, List, Optional

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

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
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
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=90)
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

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Chat completion endpoint for multi-turn conversations."""
        if not self.check_availability():
            last_msg = messages[-1]['content'] if messages else ""
            return self._fallback_response(last_msg)

        available_models = self.list_available_models()
        active_model = self.model
        if available_models and active_model not in available_models and active_model + ":latest" not in available_models:
            active_model = available_models[0]

        payload = {
            "model": active_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=90)
            if response.status_code == 200:
                msg = response.json().get("message", {})
                return msg.get("content", "").strip()
            elif response.status_code == 404:
                last_msg = messages[-1]['content'] if messages else ""
                return self._fallback_response(
                    last_msg, None,
                    f"Model '{active_model}' is not pulled in Ollama yet. Run `ollama pull {active_model}` in your terminal."
                )
            else:
                return f"⚠️ Ollama chat error {response.status_code}. Make sure model '{active_model}' is pulled."
        except Exception as e:
            return self._fallback_response(messages[-1]['content'] if messages else "", None, str(e))

    def _fallback_response(self, user_prompt: str, system_prompt: Optional[str] = None, err_msg: str = "") -> str:
        """
        Intelligent local fallback generator if Ollama is not active locally.
        Provides realistic, structured assistance while indicating local Ollama status.
        """
        prompt_lower = user_prompt.lower()
        
        fallback_notice = (
            "\n\n*💡 Note: Ollama is currently disconnected on `http://localhost:11434`. "
            "To enable live open-source LLM generation, run `ollama serve` and `ollama pull llama3.2` on your system.*"
        )

        system_lower = (system_prompt or "").lower()
        if "corporate strategy" in system_lower or "company strategy" in prompt_lower:
            return (
                "### 🏢 Company Strategy & Financial Health Guidance\n"
                "**Immediate diagnosis**\n"
                "- Track cash balance, monthly burn, runway, gross margin, receivables, payables, customer retention, and break-even point.\n"
                "- Separate essential costs from costs that can be paused, renegotiated, or converted to variable costs.\n\n"
                "**Growth plan**\n"
                "- Focus on one profitable customer segment, one measurable value proposition, and the lowest-cost sales channel.\n"
                "- Test pricing and retention before adding headcount or expanding into new markets.\n\n"
                "**Financial or crisis plan**\n"
                "- Prepare a 13-week cash-flow forecast, collect overdue invoices, negotiate supplier terms, and protect revenue-generating operations.\n"
                "- Prioritize payroll, critical suppliers, security, legal obligations, and customer commitments. Get advice from a qualified accountant or legal adviser for regulated decisions.\n\n"
                "**Low-budget operating plan**\n"
                "- Keep a small core team, use automation and open-source tools where appropriate, remove low-return subscriptions, and review every expense weekly.\n"
                "- Set weekly owners and targets for cash collection, sales, delivery, and customer retention.\n\n"
                "**Next 30 days**\n"
                "1. Build a 13-week cash-flow forecast.\n"
                "2. Rank every expense by business impact.\n"
                "3. Contact key customers and overdue accounts.\n"
                "4. Choose one growth experiment and measure its result."
                + fallback_notice
            )
        elif "career counsellor" in system_lower or "career counselling" in prompt_lower:
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
                "3. **RAG & Vector Storage**: Qdrant, Chroma, FastEmbed, and Chunking Strategies.\n"
                "4. **Local LLM Integration**: Ollama, HuggingFace Transformers, vLLM.\n"
                "5. **Production Backend**: FastAPI, Docker, Async Queues, and Monitoring.\n\n"
                "**Recommended Action**: Build a end-to-end RAG project combining Qdrant + FastAPI."
                + fallback_notice
            )
        elif "interview" in prompt_lower or "question" in prompt_lower:
            return (
                "### 🎤 Technical Interview Question\n"
                "**Question**: Explain how Retrieval-Augmented Generation (RAG) improves LLM factual accuracy compared to standard zero-shot prompting.\n\n"
                "**Key points to touch upon**:\n"
                "- Grounding responses in domain-specific documents\n"
                "- Vector embedding similarity search using cosine distance in Qdrant\n"
                "- Mitigating hallucinations by providing explicit context in system prompt"
                + fallback_notice
            )
        elif "recruitment" in prompt_lower or "hiring" in prompt_lower or "candidate" in prompt_lower:
            return (
                "### 💼 Business Recruitment Guidance\n"
                "When evaluating senior technical candidates:\n"
                "- **Technical Competency**: Review hands-on system architecture experience and GitHub projects.\n"
                "- **Problem Solving**: Evaluate candidate trade-off analysis between local inference (Ollama) vs cloud API latency.\n"
                "- **Culture Fit**: Look for continuous learning and clear technical communication."
                + fallback_notice
            )
        else:
            return (
                f"### 🤖 Ardhanarishwar AI Assistant\n"
                f"Thank you for your question: *\"{user_prompt[:80]}\"*\n\n"
                f"I am ready to assist you with Career Planning, Resume ATS Scoring, Mock Interviews, and Business Recruitment workflows.\n"
                + fallback_notice
            )

# Global LLM instance
llm_client = OllamaLLM()
