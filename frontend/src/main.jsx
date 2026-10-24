import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ArrowRight, ArrowUpRight, BookOpen, Check, ChevronRight, Clock3, Code2, Download, FileText, Layers3, Loader2, Plus, RotateCcw, Sparkles, Upload, X } from 'lucide-react';
import './styles.css';

async function api(path, options) {
  let response;
  try { response = await fetch('/api' + path, options); }
  catch { throw new Error('Cannot reach the backend. Start FastAPI on port 8000 and try again.'); }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Please check the form and try again.');
  }
  return response.json();
}
const roles = { ml: 'AI / ML Engineer', backend: 'Backend Engineer' };
const post = body => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

function App() {
  const [tab, setTab] = useState('interview');
  const [health, setHealth] = useState(null);
  const [session, setSession] = useState(null);
  const [history, setHistory] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [answer, setAnswer] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('ml');
  const [total, setTotal] = useState(5);
  const [file, setFile] = useState(null);
  const [kbRole, setKbRole] = useState('ml');
  const [kbFile, setKbFile] = useState(null);
  const input = useRef();
  const draftKey = session ? 'screenwise-answer-' + session.questions.at(-1)?.id : '';

  async function refresh() {
    const [h, k, s] = await Promise.all([api('/health'), api('/knowledge'), api('/sessions')]);
    setHealth(h); setKnowledge(k.sources); setHistory(s);
  }
  async function run(fn) {
    setBusy(true); setError(''); setNotice('');
    try { await fn(); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function load(id) {
    const value = await api('/sessions/' + id);
    setSession(value); setTab('interview'); localStorage.setItem('screenwise-session', id);
  }
  useEffect(() => { run(async () => {
    await refresh();
    const id = localStorage.getItem('screenwise-session');
    if (id) { try { await load(id); } catch { localStorage.removeItem('screenwise-session'); } }
  }); }, []);
  useEffect(() => { setAnswer(draftKey ? localStorage.getItem(draftKey) || '' : ''); }, [draftKey]);
  function updateAnswer(value) { setAnswer(value); if (draftKey) localStorage.setItem(draftKey, value); }
  function reset() { setSession(null); setAnswer(''); localStorage.removeItem('screenwise-session'); setTab('interview'); }
  async function start(e) {
    e.preventDefault();
    await run(async () => {
      const data = new FormData(); data.append('name', name); data.append('role', role);
      data.append('total_questions', total); data.append('resume', file);
      const value = await api('/sessions', { method: 'POST', body: data });
      setSession(value); localStorage.setItem('screenwise-session', value.id); await refresh();
    });
  }
  async function submit(e) {
    e.preventDefault();
    await run(async () => {
      const value = await api(`/sessions/${session.id}/answers`, post({ question_id: session.questions.at(-1).id, answer }));
      localStorage.removeItem(draftKey); setSession(value); setAnswer(''); await refresh();
    });
  }
  async function ingest(e) {
    e.preventDefault();
    await run(async () => {
      const data = new FormData(); data.append('role', kbRole); data.append('file', kbFile);
      const result = await api('/knowledge', { method: 'POST', body: data });
      await refresh(); setNotice(`Indexed ${result.chunks} chunks from ${result.source}. Ready for retrieval.`);
    });
  }
  const completed = session?.status === 'completed';
  const current = session?.questions.at(-1);
  const step = !session ? 1 : completed ? 3 : 2;

  return <div className="shell">
    <aside className="sidebar">
      <a className="brand" href="/" onClick={e => { e.preventDefault(); setTab('interview'); }}><span className="brand-icon"><Layers3 size={23}/></span>screenwise<span className="brand-dot">.</span></a>
      <div className="workspace-label">CANDIDATE WORKSPACE</div>
      <nav>
        <button className={tab === 'interview' ? 'selected' : ''} onClick={() => setTab('interview')}><Sparkles size={18}/> Interview studio <ChevronRight size={14}/></button>
        <button className={tab === 'knowledge' ? 'selected' : ''} onClick={() => setTab('knowledge')}><BookOpen size={18}/> Knowledge base <span className="small-count">{knowledge.length}</span></button>
        <button className={tab === 'history' ? 'selected' : ''} onClick={() => setTab('history')}><Clock3 size={18}/> Past interviews</button>
      </nav>
      <div className="sidebar-note"><span className="tiny-icon"><BookOpen size={18}/></span><h4>Every question has a source.</h4><p>Resume context meets role-specific knowledge. See the reasoning behind your interview.</p><button onClick={() => setTab('knowledge')}>Explore the knowledge base <ArrowUpRight size={14}/></button></div>
      <div className="sidebar-bottom"><span className={'status-dot ' + (!health ? 'offline' : '')}/>{health ? 'Backend connected' : 'Connecting to backend'}<span className="version">v1.0</span></div>
    </aside>
    <div className="main-shell">
      <header><div>Workspace <ChevronRight size={13}/><span>{tab === 'knowledge' ? 'Knowledge base' : tab === 'history' ? 'Past interviews' : 'Interview studio'}</span></div><span className="header-badge">INTERN ASSIGNMENT <span> / </span> PGAGI</span></header>
      <main>
        {error && <div className="alert error" role="alert">{error}<button onClick={() => setError('')} aria-label="Dismiss error"><X size={16}/></button></div>}
        {notice && <div className="alert success" role="status"><Check size={17}/>{notice}</div>}
        {tab === 'interview' && <>
          <div className="page-heading"><div><div className="eyebrow">A LITTLE CONTEXT. A BETTER CONVERSATION.</div><h1>{completed ? 'Your interview, in review.' : session ? 'Let’s talk through your thinking.' : 'Your experience. Your interview.'}</h1><p>{session ? `${session.name} · ${roles[session.role]} · ${session.total_questions} questions` : 'A technical conversation shaped by your resume and the role you want.'}</p></div><span className="subtle-icon"><Sparkles size={25}/></span></div>
          <div className="steps">{['Set the context', 'Have the conversation', 'Review your session'].map((label, i) => <React.Fragment key={label}><div className={step === i + 1 ? 'active' : step > i + 1 ? 'done' : ''}><span>{step > i + 1 ? <Check size={14}/> : `0${i + 1}`}</span>{label}</div>{i < 2 && <div className="step-line"/>}</React.Fragment>)}</div>
          {!session ? <div className="setup-grid"><form className="card setup-card" onSubmit={start}>
            <div className="card-heading"><span className="section-number">01</span><div><h2>Start with your story</h2><p>A few details are all we need to get started.</p></div></div>
            <label htmlFor="name">Your name</label><input id="name" value={name} maxLength={100} onChange={e => setName(e.target.value)} placeholder="e.g. Alex Morgan" required/>
            <label>Choose your target role</label><div className="role-grid">{Object.entries(roles).map(([id, label]) => <button type="button" key={id} aria-pressed={role === id} className={'role-card ' + (role === id ? 'chosen' : '')} onClick={() => setRole(id)}><span className="role-top">{id === 'ml' ? <Sparkles size={21}/> : <Code2 size={21}/>}<span className="radio">{role === id && <span/>}</span></span><strong>{label}</strong><small>{id === 'ml' ? 'Models, data & applied thinking' : 'APIs, systems & architecture'}</small></button>)}</div>
            <label htmlFor="resume">Your resume <span className="optional-label">PDF or text · up to 25 MB</span></label>
            <input id="resume" className="file-input" ref={input} type="file" accept=".pdf,.txt" onChange={e => setFile(e.target.files[0] || null)}/>
            <button type="button" className={'upload-zone ' + (file ? 'has-file' : '')} onClick={() => input.current.click()}><span className="upload-icon">{file ? <FileText size={22}/> : <Upload size={22}/>}</span><strong>{file ? file.name : 'Choose your resume'}</strong><span>{file ? 'Click to choose a different file' : 'Give your interview a starting point'}</span><span className="browse-tag">{file ? 'Change file' : 'Browse files'} <Plus size={13}/></span></button>
            <div className="form-bottom"><div><label htmlFor="total">Interview length</label><select id="total" value={total} onChange={e => setTotal(Number(e.target.value))}>{[3, 5, 8].map(n => <option key={n} value={n}>{n} questions</option>)}</select></div><span><Clock3 size={15}/>About {total * 2}–{total * 3} minutes</span></div>
            <button className="primary start-button" disabled={busy || !file || !name.trim()}>{busy ? <><Loader2 className="spin" size={18}/> Preparing your first question…</> : <>Build my interview <ArrowRight size={18}/></>}</button><p className="privacy-note">Your session is saved locally. You can pick up where you left off.</p>
          </form><div className="right-column"><div className="context-card"><div className="eyebrow">THOUGHTFUL BY DESIGN</div><h2>More than a<br/>list of questions.</h2><p>A conversation that connects what you’ve done with what the role needs.</p><div className="flow-visual"><div><FileText size={20}/><span>Your resume</span></div><span className="flow-plus">+</span><div><BookOpen size={20}/><span>Role knowledge</span></div><div className="flow-connector"/><div className="flow-result"><Sparkles size={18}/> A contextual interview</div></div><ul>{[['Made for your background', 'Skills and projects guide the conversation.'], ['Grounded in real knowledge', 'Retrieved passages keep questions connected.'], ['A clear record of your thinking', 'Review answers and source context together.']].map(([title, desc]) => <li key={title}><Check size={15}/><div><strong>{title}</strong><p>{desc}</p></div></li>)}</ul></div><div className="mode-card"><span className="status-dot"/><div><strong>{health?.demo ? 'Offline demo is enabled' : health ? `${health.llm_provider} generation is configured` : 'Checking configuration…'}</strong><p>{health?.demo ? 'No key needed. Enable OpenAI and upload a textbook for the full RAG experience.' : 'Questions use your configured model. API usage may incur charges.'}</p></div></div></div></div> : completed ? <>
            <section className="card report-card"><div className="report-title"><span className="report-check"><Check size={26}/></span><div><h2>Conversation complete</h2><p>Your answers and their source context are saved.</p></div><a className="secondary" href={`/api/sessions/${session.id}/export`} download><Download size={16}/> Export JSON</a></div><div className="report-stats"><div><strong>{session.report.answered}</strong><span>Answers recorded</span></div><div><strong>{session.report.topics.length}</strong><span>Topics explored</span></div><div><strong>{session.resume.difficulty}</strong><span>Starting difficulty</span></div></div><p className="report-note">{session.report.note}</p></section>
            {session.questions.map((q, i) => <section className="card transcript" key={q.id}><div className="eyebrow">QUESTION {i + 1} · {q.topic}</div><h3>{q.question}</h3><div className="saved-answer">{q.answer}</div><div className="observation"><strong>Review note</strong><p>{session.report.observations[i].observation}</p><span>{session.report.observations[i].word_count} words · Literal concepts mentioned: {session.report.observations[i].mentioned_concepts.join(', ') || 'none detected'}</span></div><Sources question={q}/></section>)}<button className="primary" onClick={reset}><Plus size={17}/> Start another interview</button>
          </> : <div className="interview-grid"><div><section className="card question-card"><div className="question-meta"><span className="pill">QUESTION {session.questions.length} OF {session.total_questions}</span><span>{session.resume.difficulty}</span></div><div className="progress"><span style={{ width: `${session.questions.filter(q => q.answer).length / session.total_questions * 100}%` }}/></div><div className="eyebrow">{current.topic}</div><h2>{current.question}</h2><p className="rationale">{current.rationale}</p><form onSubmit={submit}><label htmlFor="answer">Your answer</label><textarea id="answer" value={answer} onChange={e => updateAnswer(e.target.value)} maxLength={10000} placeholder="Walk through your approach, share an example, and explain your tradeoffs…" required rows={9}/><div className="answer-footer"><span>{answer.trim().split(/\s+/).filter(Boolean).length} words · Draft saved in this browser</span><button className="primary" disabled={busy || !answer.trim()}>{busy ? <Loader2 size={17} className="spin"/> : null}{session.questions.length === session.total_questions ? 'Finish & review' : 'Save & continue'}<ArrowRight size={17}/></button></div></form></section>{session.questions.slice(0, -1).map((q, i) => <details className="card previous" key={q.id}><summary>Question {i + 1} · {q.topic}<Check size={16}/></summary><h3>{q.question}</h3><p>{q.answer}</p></details>)}</div><aside className="interview-context"><section className="card"><div className="eyebrow">RESUME CONTEXT</div><h3>{session.name}</h3><div className="tags">{session.resume.skills.length ? session.resume.skills.map(s => <span key={s}>{s}</span>) : <span>No known skills detected</span>}</div><p>{session.resume.projects[0] || 'The role knowledge guides this interview.'}</p></section><section className="card"><BookOpen size={22}/><h3>Behind this question</h3><p>Inspect the retrieved passages and query used to generate this question.</p><Sources question={current}/><span className="provider-label">{current.provider} · {current.model}</span></section><button className="text-button" onClick={reset}><RotateCcw size={14}/> Save for later & start new</button></aside></div>}
        </>}
        {tab === 'knowledge' && <><div className="page-heading"><div><div className="eyebrow">THE CONTEXT BEHIND THE CONVERSATION</div><h1>Your knowledge library.</h1><p>Upload a role-specific textbook to ground your interview in its content.</p></div><BookOpen size={30}/></div><div className="alert info">The included notes are demonstration content. For the assignment, upload one of the supplied ML textbooks and select AI / ML Engineer. Scanned PDFs need OCR before upload.</div><form className="card knowledge-form" onSubmit={ingest}><h2>Add a knowledge source</h2><label htmlFor="kb-role">Use for role</label><select id="kb-role" value={kbRole} onChange={e => setKbRole(e.target.value)}>{Object.entries(roles).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select><label htmlFor="kb-file">Textbook or document</label><input id="kb-file" type="file" accept=".pdf,.txt,.md" required onChange={e => setKbFile(e.target.files[0])}/><p>PDF, TXT or Markdown · 25 MB maximum · 220-word chunks with 45-word overlap</p><button className="primary" disabled={busy || !kbFile}>{busy ? <Loader2 className="spin" size={17}/> : <Upload size={17}/>} {busy ? 'Embedding & indexing…' : 'Index document'}</button></form><div className="library-grid">{knowledge.map(s => <div className="card source-card" key={s.role + s.source}><BookOpen size={22}/><span className="pill">{s.kind}</span><h3>{s.source}</h3><p>{roles[s.role]}</p><span>{s.chunks} indexed chunks</span></div>)}</div>{!knowledge.length && <p>No sources for the configured embedding model yet. Upload a textbook to get started.</p>}<p className="footnote">Embedding provider: {health?.embedding_provider}. Changing the provider creates a separate index; upload sources again.</p></>}
        {tab === 'history' && <><div className="page-heading"><div><div className="eyebrow">PICK UP THE CONVERSATION</div><h1>Your past interviews.</h1><p>Saved sessions stay available after you restart the app.</p></div><button className="primary" onClick={reset}><Plus size={16}/> New interview</button></div><div className="card history-card">{history.length ? history.map(s => <button key={s.id} disabled={busy} onClick={() => run(() => load(s.id))}><span className="history-avatar">{s.name[0].toUpperCase()}</span><div><strong>{s.name}</strong><p>{roles[s.role]} · {new Date(s.created_at).toLocaleDateString()}</p></div><span className={'pill ' + s.status}>{s.status}</span><ChevronRight size={17}/></button>) : <div className="empty"><Clock3 size={28}/><h3>Your first conversation starts here.</h3><p>Start an interview and it will appear in this list.</p><button className="primary" onClick={reset}>Start an interview <ArrowRight size={16}/></button></div>}</div></>}
        <footer><span>screenwise<span className="brand-dot">.</span></span><p>Built for thoughtful technical conversations.</p><span>RESUME → RETRIEVAL → INTERVIEW</span></footer>
      </main>
    </div>
  </div>;
}
function Sources({ question }) {
  return <details className="sources"><summary><BookOpen size={15}/> View retrieval trace <ChevronRight size={14}/></summary><div className="query"><strong>Retrieval query</strong><p>{question.query}</p></div>{question.sources.map(s => <div className={'source-excerpt ' + (question.source_ids.includes(s.id) ? 'cited' : '')} key={s.id}><strong>{s.source} · page {s.page}</strong><small>Similarity {s.score.toFixed(3)}{question.source_ids.includes(s.id) ? ' · Cited by generator' : ''}</small><p>{s.text}</p></div>)}</details>;
}
createRoot(document.getElementById('root')).render(<App/>);
