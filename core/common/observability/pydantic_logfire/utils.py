def final_output_attributes(query: str, final_output: str) -> dict:
    '''Attribute template for logging a final user/assistant turn in Logfire's Messages UI.'''
    return {
        'gen_ai.input.messages': [
            {'role': 'user', 'parts': [{'type': 'text', 'content': query}]},
        ],
        'gen_ai.output.messages': [
            {
                'role': 'assistant',
                'parts': [{'type': 'text', 'content': final_output}],
            },
        ],
    }
