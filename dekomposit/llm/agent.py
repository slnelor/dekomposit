import json
import logging
import httpx
from pathlib import Path
from typing import Any, AsyncGenerator, cast

from dekomposit.llm.base_client import Client
from dekomposit.llm.types import AgentResponse, ToolDecision, LanguageDetection
from dekomposit.llm.tools.registry import ToolRegistry
from dekomposit.llm.formatting import FormatRegistry
from dekomposit.llm.memory import UserMemory
from dekomposit.llm.prompts import PromptRegistry


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Agent:
    """Base agent class with LLM client, memory, prompt management, and tool registry."""

    def __init__(
        self,
        model: str | None = None,
        server: str | None = None,
        user_id: int | None = None,
    ) -> None:
        """Initialize agent with LLM client, tool registry, and empty state.

        Args:
            model: LLM model to use (defaults to config)
            server: LLM server URL (defaults to config)
            user_id: User ID for memory tracking (defaults to None for anonymous)
        """
        self.client = Client(model=model, server=server)
        self.messages: list[dict] = []
        self.custom_personality: dict[str, str] = {}
        self.registry = ToolRegistry(auto_discover=True)
        self.formats = FormatRegistry()
        self.prompts = PromptRegistry()
        self.user_id = user_id
        self.memory = UserMemory(user_id=user_id)
        self._load_memory()
        self.base_prompts = self._load_base_prompts()
        self.base_prompt = self._build_base_prompt(self.base_prompts)
        self.routing_prompt = self._build_routing_prompt()
        self.detection_prompt = self.prompts.get("detection") or ""

        logger.info(f"Agent initialized with model: {self.client.model}")
        logger.info(f"Available tools: {self.registry.list_tools()}")
        logger.info(f"Tool schemas: {len(self.registry.get_tool_schemas())} available")

    async def execute_tools(self, text: str, max_iterations: int = 5) -> dict[str, Any]:
        """Main agentic loop: LLM decides tools → executes → observes → repeats.
        
        This is the core of the agentic architecture - the LLM sees tool results
        and decides what to do next.
        
        Args:
            text: User input text
            max_iterations: Maximum number of loop iterations
            
        Returns:
            Dict with type and message/tool_calls
        """
        messages: list[dict] = [
            {"role": "system", "content": self.base_prompt}
        ]
        messages.append({"role": "user", "content": text})
        
        tool_call_history: list[dict] = []
        
        for iteration in range(max_iterations):
            logger.debug(f"Agent loop iteration {iteration + 1}/{max_iterations}")
            
            # Get available tools
            tools = self.registry.get_tool_schemas()
            
            # LLM decides what to do
            response = await self.client.request_with_tools(
                messages=messages,
                tools=tools if tools else None,
            )
            
            message = response.choices[0].message
            
            # Debug: log the message details
            logger.debug(f"Message content: {message.content}")
            logger.debug(f"Message tool_calls: {message.tool_calls}")
            
            # Check for tool calls
            tool_calls = message.tool_calls
            
            # Handle case where tool_calls is None or empty
            if not tool_calls:
                # No tool calls - LLM has final response
                final_message = message.content or ""
                logger.debug(f"Agent loop complete: {final_message[:100]}...")
                return {
                    "type": "response",
                    "message": final_message,
                    "tool_calls": tool_call_history,
                }
            
            # Fix for Gemini: add content if empty when tool_calls present
            if not message.content:
                message.content = "[TOOL CALL]"
            
            logger.info(f"LLM requested {len(tool_calls)} tool call(s)")
            
            # Debug: print messages count
            logger.debug(f"Messages before adding assistant: {len(messages)}")
            
            # IMPORTANT: Add assistant message with tool_calls to messages
            # This is required for the model to know which tool calls we're responding to
            assistant_message = {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id if tc.id else tc.function.name,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in tool_calls
                ]
            }
            messages.append(assistant_message)
            logger.debug(f"Messages after adding assistant: {len(messages)}")
            
            # Execute each tool call
            for tc in tool_calls:
                tool_name = tc.function.name
                
                # Fix for Gemini: use function name as fallback if id is empty
                tool_call_id = tc.id if tc.id else tool_name
                
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Get and execute tool
                tool = self.registry.get(tool_name)
                if tool is None:
                    logger.warning(f"Tool not found: {tool_name}")
                    tool_result = {"error": f"Tool not found: {tool_name}"}
                else:
                    try:
                        tool_result = await tool(**tool_args)
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        tool_result = {"error": str(e)}
                
                # Add tool result to messages (LLM sees it!)
                # Include name for Gemini compatibility
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(tool_result),
                }
                
                messages.append(tool_message)
                
                # Track for history
                tool_call_history.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": tool_result,
                })
                
                logger.debug(f"Tool result: {tool_result}")
            
            # Loop continues - LLM sees tool results and decides next action
        
        logger.warning("Max iterations reached in agent loop")
        return {
            "type": "error",
            "message": "Maximum iterations reached",
            "tool_calls": tool_call_history,
        }

    def _load_memory(self) -> None:
        """Load user memory from storage. Currently a stub - returns defaults."""
        # TODO: Integrate with database to load persisted memory
        # For now, memory starts empty/default as per spec
        logger.debug(f"Loaded memory for user {self.user_id or 'anonymous'}")
        pass

    def _load_base_prompts(self) -> dict[str, str]:
        """Read all prompt files from base_prompts/ directory.

        Returns:
            Dict mapping filenames to their contents
            Example: {'SOUL.md': '# SOUL.md...', 'MEMORY.md': '...'}
        """
        prompts = {}
        prompting_dir = Path(__file__).parent / "base_prompts"

        if not prompting_dir.exists():
            logger.warning(f"Base prompts directory not found: {prompting_dir}")
            return prompts

        for file_path in prompting_dir.glob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                prompts[file_path.name] = content
                logger.debug(f"Loaded prompt file: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to read {file_path.name}: {e}")

        logger.info(f"Loaded {len(prompts)} prompt files: {list(prompts.keys())}")
        return prompts

    def _build_base_prompt(self, prompts: dict[str, str]) -> str:
        """Aggregate SOUL and MEMORY prompts into a single system prompt."""
        sections: list[str] = []
        
        soul_content = prompts.get("SOUL.md", "").strip()
        if soul_content:
            try:
                custom_soul = self.custom_personality.get("SOUL.md", "")
                if custom_soul:
                    soul_content = soul_content.replace("{custom_personality['SOUL.md']}", custom_soul)
                else:
                    soul_content = soul_content.replace("{custom_personality['SOUL.md']}", "")
                soul_content = soul_content.format(custom_personality=self.custom_personality)
            except Exception as e:
                logger.warning(f"Failed to format SOUL: {e}")
            sections.append(soul_content)
        
        memory_content = prompts.get("MEMORY.md", "").strip()
        if memory_content:
            try:
                custom_mem = self.custom_personality.get("MEMORY.md", "")
                if custom_mem:
                    memory_content = memory_content.replace("{custom_personality['MEMORY.md']}", custom_mem)
                else:
                    memory_content = memory_content.replace("{custom_personality['MEMORY.md']}", "")
                
                memory_content = memory_content.replace("{learning_gaps}", ", ".join(self.memory.learning_gaps) if self.memory.learning_gaps else "Still learning...")
                memory_content = memory_content.replace("{topics}", ", ".join(self.memory.topics) if self.memory.topics else "Nothing specific yet")
                memory_content = memory_content.replace("{teaching_style}", self.memory.teaching_style)
                memory_content = memory_content.replace("{speaking_style}", self.memory.speaking_style)
                memory_content = memory_content.replace("{tone_vibe}", self.memory.tone_vibe)
                memory_content = memory_content.replace("{conversation_history}", self._get_conversation_summary())
            except Exception as e:
                logger.warning(f"Failed to format memory: {e}")
                memory_content = ""
            
            if memory_content and memory_content.strip():
                sections.append(memory_content)
        
        return "\n\n".join(sections).strip()

    def _get_conversation_summary(self) -> str:
        """Get a summary of recent conversation for memory injection."""
        if not self.memory.conversation_history:
            return "No history yet"
        
        recent = self.memory.conversation_history[-10:]
        lines = []
        for msg in recent:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if len(content) > 100:
                content = content[:100] + "..."
            lines.append(f"- {role}: {content}")
        return "\n".join(lines)

    def _build_routing_prompt(self) -> str:
        """Build dynamic routing prompt from prompts registry."""
        tool_names = self.registry.list_tools()
        tool_list = ", ".join(tool_names) if tool_names else "none"
        
        routing_template = self.prompts.get("routing")
        if routing_template:
            return routing_template.format(tools=tool_list)
        
        # Fallback - should not happen if prompt file exists
        return f"You are a routing assistant. Available tools: {tool_list}. Decide action."

    async def handle_message(self, text: str) -> dict[str, Any] | None:
        """Route a user message through tool selection and response formatting.
        
        Uses agentic loop - LLM decides tools, executes them, observes results,
        and continues until final response.
        """
        self.memory.add_message("user", text)
        
        # Use agentic loop - LLM decides what tools to use
        result = await self.execute_tools(text)
        
        if result.get("type") == "response":
            # Update memory with the interaction
            message = result.get("message", "")
            if message:
                self.memory.add_message("assistant", message)
                self._rebuild_base_prompt()
        
        return result

    async def chat(self, text: str) -> str:
        """Entrypoint for chat: returns formatted response string."""
        result = await self.handle_message(text)
        if result is None:
            return "Sorry, I couldn't process that."

        if result["type"] == "translation":
            return self.format_translation(result)
        elif result["type"] == "response":
            return result["message"]

        return str(result)

    async def stream_chat(self, text: str) -> AsyncGenerator[str, None]:
        """Streaming chat entrypoint: yields response chunks."""
        self.memory.add_message("user", text)
        
        decision = await self._decide_action(text)

        if decision.action == "translate":
            result = await self._handle_translation(decision)
            if result is None:
                yield "Sorry, I couldn't process that."
                return
            yield self.format_translation(result)
            self._update_memory_on_translation(decision, result)
            return

        async for chunk in self._handle_response_stream(decision):
            yield chunk

    def _update_memory_on_translation(
        self, decision: ToolDecision, result: dict[str, Any]
    ) -> None:
        """Update memory based on translation interaction."""
        text = decision.text.lower()
        
        if decision.source_lang and decision.target_lang:
            topics_detected = self._extract_topics_from_text(text)
            for topic in topics_detected:
                self.memory.add_topic(topic)
        
        self._rebuild_base_prompt()

    def _update_memory_on_response(
        self, decision: ToolDecision, result: dict[str, Any]
    ) -> None:
        """Update memory based on conversation response."""
        user_text = decision.text.lower()
        agent_text = result.get("message", "").lower()
        
        topics = self._extract_topics_from_text(user_text)
        for topic in topics:
            self.memory.add_topic(topic)
        
        self._detect_and_update_style(user_text, agent_text)
        
        self.memory.add_message("assistant", result.get("message", ""))
        
        self._rebuild_base_prompt()

    def _rebuild_base_prompt(self) -> None:
        """Rebuild base prompt with updated memory."""
        self.base_prompt = self._build_base_prompt(self._load_base_prompts())
        logger.debug("Rebuilt base prompt with updated memory")

    def _extract_topics_from_text(self, text: str) -> list[str]:
        """Extract potential topics from text."""
        topic_keywords = {
            "weather": ["weather", "sun", "rain", "snow", "hot", "cold", "temperature"],
            "food": ["food", "eat", "cook", "restaurant", "recipe", "breakfast", "lunch", "dinner"],
            "travel": ["travel", "trip", "vacation", "flight", "hotel", "country", "city"],
            "work": ["work", "job", "office", "meeting", "boss", "colleague"],
            "family": ["family", "mother", "father", "brother", "sister", "kid", "child"],
            "sports": ["sport", "football", "tennis", "run", "gym", "exercise"],
            "music": ["music", "song", "band", "concert", "play"],
            "movies": ["movie", "film", "watch", "series", "show"],
            "technology": ["tech", "computer", "phone", "internet", "ai", "software"],
        }
        
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                found_topics.append(topic)
        
        return found_topics

    def _detect_and_update_style(self, user_text: str, agent_text: str) -> None:
        """Detect and update speaking/teaching style preferences."""
        user_words = len(user_text.split())
        
        if user_words < 5:
            self.memory.set_speaking_style("short")
        elif user_words > 30:
            self.memory.set_speaking_style("detailed")
        
        if "explain" in user_text or "what is" in user_text or "why" in user_text:
            self.memory.set_teaching_style("explanation")
        elif "practice" in user_text or "exercise" in user_text or "quiz" in user_text:
            self.memory.set_teaching_style("practice")

    def format_translation(self, result: dict[str, Any]) -> str:
        """Format translation result using format registry."""
        source = result.get("source_lang", "").upper()
        target = result.get("target_lang", "").upper()
        translation = result.get("translation", "")

        return self.formats.render(
            None,
            source=source,
            target=target,
            translation=translation,
        )

    async def _detect_language(self, text: str) -> str | None:
        """Detect language using LLM."""
        messages = [
            {
                "role": "system",
                "content": self.detection_prompt or "Detect the language of the following text. Return language code: en, ru, uk, sk, or other.",
            },
            {
                "role": "user",
                "content": text,
            },
        ]

        try:
            response = await self.client.request(
                messages=messages, return_format=LanguageDetection
            )
            detected = cast(LanguageDetection | None, response.choices[0].message.parsed)
            if detected:
                logger.debug(f"LLM detected language: {detected.language} (confidence: {detected.confidence})")
                if detected.language in {"en", "ru", "uk", "sk"}:
                    return detected.language
        except Exception as e:
            logger.warning(f"LLM language detection failed: {e}")

        return None

    async def _decide_action(self, text: str) -> ToolDecision:
        """Use the LLM to decide whether to translate or respond."""
        messages = [
            {
                "role": "system",
                "content": self.routing_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ]

        response = await self.client.request(
            messages=messages, return_format=ToolDecision
        )
        decision = cast(ToolDecision | None, response.choices[0].message.parsed)
        if decision is None:
            return ToolDecision(action="translate", text=text)

        if decision.text.strip() == "":
            decision.text = text

        if decision.action not in {"translate", "respond"}:
            decision.action = "translate"

        return decision

    async def _handle_translation(
        self, decision: ToolDecision
    ) -> dict[str, Any] | None:
        """Translate using Adaptive MT datasets with local language detection."""
        text = decision.text
        valid_langs = {"en", "ru", "uk", "sk"}
        source_lang = (
            decision.source_lang if decision.source_lang in valid_langs else None
        )
        target_lang = (
            decision.target_lang if decision.target_lang in valid_langs else None
        )

        if source_lang is None:
            source_lang = await self._detect_language(text)

        if not source_lang or not target_lang:
            logger.warning("Could not resolve languages for translation")
            return None

        dataset_id = f"adaptive-{source_lang}-{target_lang}"

        tool = self.registry.get("adaptive_translation")
        if tool is None:
            logger.warning("Translation tool not found in registry")
            return None

        try:
            result = await tool(
                text,
                source_lang=source_lang,
                target_lang=target_lang,
                dataset_id=dataset_id,
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text.lower()
            if status in {400, 404} and (
                "adaptive mt dataset" in body or "not found" in body
            ):
                logger.warning("Dataset not found: %s", dataset_id)
                return None
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "adaptive mt dataset" in message or "not found" in message:
                logger.warning("Dataset not found: %s", dataset_id)
                return None
            raise

        translation = None
        response_payload = result.get("response", {})
        translations = response_payload.get("translations", [])
        if translations:
            translation = translations[0].get("translatedText")

        if not translation:
            return None

        return {
            "type": "translation",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translation": translation,
            "method": "adaptive_mt",
            "raw": response_payload,
        }

    async def _handle_response_stream(self, decision: ToolDecision) -> AsyncGenerator[str, None]:
        """Stream response using the base LLM."""
        messages = [
            {
                "role": "system",
                "content": self.base_prompt or "You are a language learning coach.",
            },
            {
                "role": "user",
                "content": decision.text,
            },
        ]

        async for chunk in self.client.stream(messages):
            yield chunk

    async def _handle_response(self, decision: ToolDecision) -> dict[str, Any]:
        """Default response using the base LLM (non-streaming)."""
        messages = [
            {
                "role": "system",
                "content": self.base_prompt or "You are a language learning coach.",
            },
            {
                "role": "user",
                "content": decision.text,
            },
        ]

        response = await self.client.request(
            messages=messages, return_format=AgentResponse
        )
        parsed = cast(AgentResponse | None, response.choices[0].message.parsed)
        text = parsed.message if parsed else ""
        return {
            "type": "response",
            "message": text,
        }
