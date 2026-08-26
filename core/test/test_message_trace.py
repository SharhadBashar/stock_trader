import os
import unittest

os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', 'test')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB', 'test')

from pydantic_ai import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
)
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from core.common.agent_trace import TurnTrace, jsonable, parse_tool_args
from db.models.messages import Message
from db.operations.messages import (
    display_content,
    history_row_fields,
    infer_agent_name,
    message_thinking,
    message_tool_responses,
    message_tools_called,
    turn_summary,
)


class MessageModelTests(unittest.TestCase):
    def test_keeps_original_columns_and_adds_trace_fields(self):
        columns = set(Message.__table__.columns.keys())
        self.assertTrue({
            'id',
            'conversation_id',
            'user_message_id',
            'sequence',
            'kind',
            'role',
            'payload',
            'display_content',
            'include_in_history',
            'status',
            'run_id',
            'created_at',
            'updated_at',
        }.issubset(columns))
        self.assertTrue({
            'user_query',
            'agents_called',
            'agent_steps',
            'tools_called',
            'tool_responses',
            'thinking',
            'agent_name',
            'model_name',
            'latency_ms',
            'is_final',
        }.issubset(columns))


class TurnTraceTests(unittest.TestCase):
    def test_records_user_turn_agents_tools_thinking_and_final(self):
        trace = TurnTrace(
            'What is AAPL doing?',
            root_agent = 'orchestrator_agent',
            root_model = 'gpt-5.6-terra',
        )

        trace.record(
            PartStartEvent(index = 0, part = ThinkingPart(content = 'I should route this.')),
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )
        trace.record(
            PartDeltaEvent(index = 0, delta = ThinkingPartDelta(content_delta = ' Call robinhood.')),
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )
        trace.record(
            PartEndEvent(
                index = 0,
                part = ThinkingPart(content = 'I should route this. Call robinhood.'),
            ),
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )

        call = FunctionToolCallEvent(
            part = ToolCallPart(
                tool_name = 'delegate_task',
                args = {'agent_name': 'robinhood_agent', 'task': 'Quote AAPL'},
                tool_call_id = 'call-1',
            )
        )
        trace.record(
            call,
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )

        trace.record(
            PartStartEvent(index = 0, part = ThinkingPart(content = 'Looking up the quote.')),
            agent_name = 'robinhood_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'robinhood',
        )
        trace.record(
            PartEndEvent(index = 0, part = ThinkingPart(content = 'Looking up the quote.')),
            agent_name = 'robinhood_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'robinhood',
        )
        equity_call = FunctionToolCallEvent(
            part = ToolCallPart(
                tool_name = 'get_quote',
                args = {'symbol': 'AAPL'},
                tool_call_id = 'call-2',
            )
        )
        trace.record(
            equity_call,
            agent_name = 'robinhood_equity_agent',
            model_name = 'claude-sonnet-5',
            buffer_key = 'equity',
        )
        equity_result = FunctionToolResultEvent(
            part = ToolReturnPart(
                tool_name = 'get_quote',
                content = {'price': 190.12},
                tool_call_id = 'call-2',
            )
        )
        trace.record(
            equity_result,
            agent_name = 'robinhood_equity_agent',
            model_name = 'claude-sonnet-5',
            buffer_key = 'equity',
        )

        parent_result = FunctionToolResultEvent(
            part = ToolReturnPart(
                tool_name = 'delegate_task',
                content = 'AAPL is 190.12',
                tool_call_id = 'call-1',
            )
        )
        trace.record(
            parent_result,
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )
        trace.record(
            PartEndEvent(index = 1, part = TextPart(content = 'AAPL is trading at 190.12')),
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
            buffer_key = 'orchestrator',
        )

        agent_names = [item['name'] for item in trace.agents_called()]
        self.assertEqual(
            agent_names,
            ['orchestrator_agent', 'robinhood_agent', 'robinhood_equity_agent'],
        )

        types = [step['type'] for step in trace.steps]
        self.assertIn('thinking', types)
        self.assertIn('tool_call', types)
        self.assertIn('tool_result', types)
        self.assertIn('agent_call', types)
        self.assertIn('text', types)

        thinking = next(step for step in trace.steps if step['type'] == 'thinking')
        self.assertEqual(thinking['agent'], 'orchestrator_agent')
        self.assertIn('robinhood', thinking['content'])

        quote_call = next(step for step in trace.tools_called() if step['tool_name'] == 'get_quote')
        self.assertEqual(quote_call['agent'], 'robinhood_equity_agent')
        self.assertEqual(quote_call['model'], 'claude-sonnet-5')
        self.assertEqual(quote_call['args'], {'symbol': 'AAPL'})

        quote_result = next(
            step for step in trace.tool_responses() if step['tool_id'] == 'call-2'
        )
        self.assertEqual(quote_result['content'], {'price': 190.12})
        self.assertEqual(quote_result['status'], 'success')
        self.assertEqual(quote_result['agent'], 'robinhood_equity_agent')

        self.assertIn('[orchestrator_agent]', trace.thinking_text())
        self.assertIn('[robinhood_agent]', trace.thinking_text())
        self.assertGreaterEqual(trace.latency_ms(), 0)

    def test_flush_keeps_unfinished_thinking(self):
        trace = TurnTrace('hello', root_agent = 'orchestrator_agent')
        trace.record(
            PartStartEvent(index = 0, part = ThinkingPart(content = 'partial')),
            agent_name = 'orchestrator_agent',
            model_name = 'gpt-5.6-terra',
        )
        trace.flush()
        self.assertEqual(trace.steps[0]['type'], 'thinking')
        self.assertEqual(trace.steps[0]['content'], 'partial')

    def test_parse_tool_args_and_jsonable(self):
        self.assertEqual(parse_tool_args('{"symbol": "AAPL"}'), {'symbol': 'AAPL'})
        self.assertEqual(parse_tool_args('not-json'), 'not-json')
        self.assertEqual(jsonable(('a', 1)), ['a', 1])


class MessageFieldTests(unittest.TestCase):
    def test_extracts_thinking_tools_and_final_summary(self):
        user = ModelRequest(parts = [UserPromptPart(content = 'Quote AAPL')])
        assistant_tools = ModelResponse(
            parts = [
                ThinkingPart(content = 'Delegate to robinhood'),
                ToolCallPart(
                    tool_name = 'delegate_task',
                    args = {'agent_name': 'robinhood_agent', 'task': 'Quote AAPL'},
                    tool_call_id = 'call-1',
                ),
            ],
            model_name = 'gpt-5.6-terra',
        )
        tool_return = ModelRequest(
            parts = [
                ToolReturnPart(
                    tool_name = 'delegate_task',
                    content = 'AAPL is 190.12',
                    tool_call_id = 'call-1',
                )
            ]
        )
        final = ModelResponse(
            parts = [TextPart(content = 'AAPL is trading at 190.12')],
            model_name = 'gpt-5.6-terra',
        )

        self.assertEqual(display_content(user), 'Quote AAPL')
        self.assertEqual(message_thinking(assistant_tools), 'Delegate to robinhood')
        self.assertEqual(
            message_tools_called(assistant_tools)[0]['called_agent'],
            'robinhood_agent',
        )
        self.assertEqual(message_tool_responses(tool_return)[0]['content'], 'AAPL is 190.12')
        self.assertEqual(infer_agent_name(assistant_tools, 'orchestrator_agent'), 'orchestrator_agent')
        self.assertIsNone(infer_agent_name(user, 'orchestrator_agent'))

        trace = TurnTrace('Quote AAPL', root_agent = 'orchestrator_agent', root_model = 'gpt-5.6-terra')
        trace.add_step({
            'type': 'thinking',
            'agent': 'orchestrator_agent',
            'model': 'gpt-5.6-terra',
            'content': 'Delegate to robinhood',
        })
        trace.add_step({
            'type': 'tool_call',
            'agent': 'orchestrator_agent',
            'model': 'gpt-5.6-terra',
            'tool_name': 'delegate_task',
            'args': {'agent_name': 'robinhood_agent', 'task': 'Quote AAPL'},
            'called_agent': 'robinhood_agent',
        })
        summary = turn_summary(trace)
        self.assertEqual(summary['agents_called'][0]['name'], 'orchestrator_agent')
        self.assertEqual(summary['agents_called'][1]['name'], 'robinhood_agent')

        final_fields = history_row_fields(
            final,
            user_query = 'Quote AAPL',
            root_agent = 'orchestrator_agent',
            is_final = True,
            include_summary = True,
            trace = trace,
            latency_ms = 1234,
        )
        self.assertTrue(final_fields['is_final'])
        self.assertEqual(final_fields['latency_ms'], 1234)
        self.assertEqual(final_fields['user_query'], 'Quote AAPL')
        self.assertEqual(final_fields['model_name'], 'gpt-5.6-terra')
        self.assertEqual(final_fields['agent_name'], 'orchestrator_agent')
        self.assertEqual(final_fields['display_content'], 'AAPL is trading at 190.12')
        self.assertEqual(len(final_fields['agent_steps']), 2)

        mid_fields = history_row_fields(
            assistant_tools,
            user_query = 'Quote AAPL',
            root_agent = 'orchestrator_agent',
            is_final = False,
            include_summary = False,
            trace = trace,
            latency_ms = 1234,
        )
        self.assertFalse(mid_fields['is_final'])
        self.assertIsNone(mid_fields['latency_ms'])
        self.assertEqual(mid_fields['thinking'], 'Delegate to robinhood')
        self.assertIsNone(mid_fields['agent_steps'])


if __name__ == '__main__':
    unittest.main()
