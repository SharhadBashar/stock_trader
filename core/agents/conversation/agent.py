from pydantic_ai import Agent
from pydantic_ai.models.fallback import FallbackModel

from core.common.pydantic_ai.models import gpt_5_6_luna

from core.agents.conversation.prompt import PROMPT
from core.agents.conversation.types import ConversationTitle


conversation_agent = Agent(
    model = FallbackModel(gpt_5_6_luna),
    name = 'conversation_agent',
    instructions = PROMPT,
    output_type = ConversationTitle,
)
