import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from agent.tools import TOOL_DEFINITIONS
from agent.prompts import SYSTEM_PROMPT
from agent.dispatcher import dispatch_tool

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class AgentLoop:
    """
    Диалоговый агент с постоянной историей.
    Пользователь → Claude → tool_use loop → текстовый ответ.
    """

    def __init__(self):
        self.history: list[dict] = []

    def run(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        while True:
            response = _client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.history,
            )

            # Добавляем ответ Claude в историю
            self.history.append({
                "role": "assistant",
                "content": response.content,
            })

            if response.stop_reason == "end_turn":
                text = next(
                    (b.text for b in response.content if hasattr(b, "text")),
                    "(нет ответа)",
                )
                return text

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    try:
                        result = dispatch_tool(block.name, block.input)
                        result_str = json.dumps(result, ensure_ascii=False, default=str)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"ОШИБКА: {e}",
                            "is_error": True,
                        })

                self.history.append({
                    "role": "user",
                    "content": tool_results,
                })
                # Продолжаем цикл — Claude обработает результаты инструментов

            else:
                # Неожиданный stop_reason
                text = next(
                    (b.text for b in response.content if hasattr(b, "text")),
                    f"(stop_reason: {response.stop_reason})",
                )
                return text

    def reset(self) -> None:
        """Сбросить историю разговора."""
        self.history = []
