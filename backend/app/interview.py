import copy
import uuid
from datetime import datetime, timezone

from .generation import build_report
from .knowledge import TOPICS


class InterviewService:
    def __init__(self, store, knowledge, generator):
        self.store, self.knowledge, self.generator = store, knowledge, generator

    def new(self, name, role, resume, total):
        session = {'id': str(uuid.uuid4()), 'name': name, 'role': role, 'resume': resume,
                   'total_questions': total, 'questions': [], 'status': 'active', 'report': None,
                   'created_at': datetime.now(timezone.utc).isoformat()}
        self.next_question(session)
        self.store.save(session)
        return session

    def next_question(self, session):
        index = len(session['questions'])
        topics = TOPICS[session['role']]
        # Resume influences the first topic and every retrieval query. Later turns diversify coverage.
        skills = session['resume']['skills']
        topic = topics[index % len(topics)]
        if index == 0 and skills:
            topic = next((t for t in topics if any(s.lower() in t.lower() for s in skills)), topic)
        previous = session['questions'][-1].get('answer', '') if session['questions'] else ''
        query = ' | '.join([session['role'], topic, ', '.join(skills),
                            ' '.join(session['resume']['projects'])[:600], previous[:400]])
        sources = self.knowledge.retrieve(session['role'], query)
        generated = self.generator.question(session, query, sources)
        session['questions'].append({'id': str(uuid.uuid4()), **generated, 'query': query,
            'sources': sources, 'answer': None, 'answered_at': None})

    def answer(self, session_id, question_id, answer):
        original = self.store.get(session_id)
        if not original:
            raise LookupError('Interview not found.')
        if original['status'] != 'active':
            raise ValueError('This interview is already complete.')
        if original['questions'][-1]['id'] != question_id:
            raise ValueError('This question is no longer current. Reload the interview.')
        # Work on a copy: next-question provider errors cannot partially save a turn.
        session = copy.deepcopy(original)
        current = session['questions'][-1]
        current['answer'], current['answered_at'] = answer, datetime.now(timezone.utc).isoformat()
        if len(session['questions']) == session['total_questions']:
            session['status'] = 'completed'
            session['report'] = build_report(session)
        else:
            self.next_question(session)
        self.store.save(session)
        return session


def candidate_view(session):
    """Hide expected concepts until the interview is complete."""
    result = copy.deepcopy(session)
    result['resume'].pop('text', None)
    if result['status'] != 'completed':
        for question in result['questions']:
            question.pop('expected_concepts', None)
    return result
