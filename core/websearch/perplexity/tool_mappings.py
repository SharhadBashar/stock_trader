from enum import Enum


class PerplexityToolType(Enum):
    SEARCH = 'search'
    ASK = 'ask'
    RESEARCH = 'research'
    REASON = 'reason'
    ALL = 'all'


PERPLEXITY_TOOLS = {
    PerplexityToolType.SEARCH: ['perplexity_search'],
    PerplexityToolType.ASK: ['perplexity_ask'],
    PerplexityToolType.RESEARCH: ['perplexity_research'],
    PerplexityToolType.REASON: ['perplexity_reason'],
    PerplexityToolType.ALL: [
        'perplexity_search',
        'perplexity_ask',
        'perplexity_research',
        'perplexity_reason',
    ],
}
