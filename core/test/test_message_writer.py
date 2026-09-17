import os
import unittest
import uuid
from contextlib import nullcontext
from types import SimpleNamespace

os.environ.setdefault('DB_USER', 'test')
os.environ.setdefault('DB_PASSWORD', 'test')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB', 'test')

from core.common.message_writer import StreamMessageWriter
from db.operations.messages import jsonable, parse_tool_args


class MemoryOps:
    def __init__(self):
        self.rows: list[SimpleNamespace] = []
        self.finished: list[dict] = []

    def append_event(self, db, **kwargs):
        row = SimpleNamespace(id = uuid.uuid4(), **kwargs)
        self.rows.append(row)
        return row

    def append_content_text(self, db, message_id, text):
        for row in self.rows:
            if row.id == message_id:
                content = dict(row.content or {})
                content['text'] = f'{content.get('text') or ''}{text}'
                row.content = content
                return row
        return None

    def update_event(self, db, message_id, **fields):
        for row in self.rows:
            if row.id == message_id:
                for key, value in fields.items():
                    setattr(row, key, value)
                return row
        return None

    def finish_turn(self, db, user_message_id, status, log = None, error_message = None):
        self.finished.append({
            'user_message_id': user_message_id,
            'status': status,
            'log': log,
            'error_message': error_message,
        })


class StreamMessageWriterTests(unittest.TestCase):
    def setUp(self):
        self.ops = MemoryOps()
        self.conversation_id = uuid.uuid4()
        self.user_message_id = uuid.uuid4()
        self.writer = StreamMessageWriter(
            self.conversation_id,
            self.user_message_id,
            agent_name = 'orchestrator_agent',
            model = 'gpt-5.6-terra',
            ops = self.ops,
            session_factory = lambda: nullcontext(SimpleNamespace()),
        )

    def test_jsonable_and_parse_tool_args(self):
        self.assertEqual(parse_tool_args('{"agent_name": "robinhood_agent"}'), {
            'agent_name': 'robinhood_agent',
        })
        self.assertEqual(jsonable(('a', 1)), ['a', 1])

    def test_disabled_writer_skips_db(self):
        writer = StreamMessageWriter(None, None, ops = self.ops)
        writer.start_text('hello')
        writer.complete('hello')
        self.assertEqual(self.ops.rows, [])
        self.assertEqual(self.ops.finished, [])

    def test_persists_thinking_tools_and_output(self):
        self.writer.start_thinking('hmm')
        self.writer.append_thinking(' more')
        self.writer.end_thinking()
        self.writer.tool_call('call-1', 'delegate_task', '{"agent_name": "liquid_agent"}')
        self.writer.tool_result('call-1', 'delegate_task', {'ok': True}, 'success')
        self.writer.start_text('Buy', 'part-1')
        self.writer.append_text(' AAPL')
        self.writer.end_text()
        self.writer.complete('Buy AAPL')

        types = [row.msg_type for row in self.ops.rows]
        self.assertEqual(types, ['thinking', 'tool_call', 'tool_result', 'agent_output'])
        self.assertEqual(self.ops.rows[0].content['text'], 'hmm more')
        self.assertEqual(self.ops.rows[0].status, 'completed')
        self.assertEqual(self.ops.rows[1].delegate_agent_name, 'liquid_agent')
        self.assertEqual(self.ops.rows[1].status, 'completed')
        self.assertEqual(self.ops.rows[2].parent_message_id, self.ops.rows[1].id)
        self.assertEqual(self.ops.rows[3].content['text'], 'Buy AAPL')
        self.assertEqual(self.ops.finished[0]['status'], 'completed')
        self.assertIn('latency_seconds', self.ops.finished[0]['log'])

    def test_fail_marks_turn_cancelled(self):
        self.writer.start_thinking('partial')
        self.writer.fail('cancelled')
        self.assertEqual(self.ops.finished[0]['status'], 'cancelled')
        self.writer.fail('error')
        self.assertEqual(len(self.ops.finished), 1)

    def test_complete_writes_final_output_when_no_text_parts(self):
        self.writer.complete('done')
        self.assertEqual(self.ops.rows[0].msg_type, 'agent_output')
        self.assertEqual(self.ops.rows[0].content['text'], 'done')


if __name__ == '__main__':
    unittest.main()
