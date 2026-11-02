
import { useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, BriefcaseBusiness, Users, FileCheck2,
  CalendarDays, RefreshCw, Search, ShieldCheck, ArrowUpRight,
  ChevronRight, ScanLine
} from 'lucide-react';
import { getJSON } from './services/api';
import type {
  Dashboard, Application, Issue, Requisition, Interview, Offer
} from './types';

const money = (n: number) => new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0
}).format(n);

const nav = [
  ['Overview', Activity],
  ['Applications', Users],
  ['Requisitions', BriefcaseBusiness],
  ['Interviews', CalendarDays],
  ['Offers', FileCheck2],
  ['Exceptions', AlertTriangle]
] as const;

type ScreeningResult = {
  score: number;
  skill_match: number;
  experience_score: number;
  threshold: number;
  decision: string;
  matched_skills: number;
  required_skills: number;
};

export default function App() {
  const [tab, setTab] = useState('Overview');
  const [data, setData] = useState<Dashboard | null>(null);
  const [apps, setApps] = useState<Application[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [reqs, setReqs] = useState<Requisition[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState('');

  // Stores the screening response for the result modal.
  const [screeningResult, setScreeningResult] =
    useState<ScreeningResult | null>(null);

  async function load() {
    setBusy(true);
    setError('');

    try {
      const [d, a, i, r, iv, o] = await Promise.all([
        getJSON<Dashboard>('/dashboard'),
        getJSON<Application[]>('/applications'),
        getJSON<Issue[]>('/issues'),
        getJSON<Requisition[]>('/requisitions'),
        getJSON<Interview[]>('/interviews'),
        getJSON<Offer[]>('/offers')
      ]);

      setData(d);
      setApps(a);
      setIssues(i);
      setReqs(r);
      setInterviews(iv);
      setOffers(o);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to connect to API');
    } finally {
      setBusy(false);
    }
  }

  async function scan() {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/issues/scan`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error(await response.text());

      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Issue scan failed');
    }
  }

  // Screen an application and show the result in the custom modal.
  async function scoreApplication(id: number) {
    try {
      setError('');

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/applications/${id}/screen`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const result: ScreeningResult = await response.json();

      setScreeningResult(result);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Screening failed');
    }
  }

  useEffect(() => {
    load();
  }, []);

  const visible = useMemo(() => apps.filter(a =>
    `${a.candidate} ${a.application_id} ${a.requisition}`
      .toLowerCase()
      .includes(search.toLowerCase())
  ), [apps, search]);

  const pageTitle = tab === 'Overview' ? 'Hiring overview' : tab;

  const stats = [
    {
      label: 'Open requisitions',
      value: data?.requisitions ?? '—',
      icon: BriefcaseBusiness,
      note: 'Roles accepting applicants',
      tone: 'blue'
    },
    {
      label: 'Candidates',
      value: data?.candidates ?? '—',
      icon: Users,
      note: 'Profiles in the workspace',
      tone: 'violet'
    },
    {
      label: 'Applications',
      value: data?.applications ?? '—',
      icon: FileCheck2,
      note: 'Across every stage',
      tone: 'mint'
    },
    {
      label: 'Interviews',
      value: data?.interviews ?? '—',
      icon: CalendarDays,
      note: 'Recorded interview rounds',
      tone: 'orange'
    }
  ];

  return (
    <div className="app-shell">
      <aside className="rail">
        <div className="brand-lockup">
          <div className="brand-mark">H<span>.</span></div>
          <div>
            <strong>hireflow</strong>
            <small>INTELLIGENCE PLATFORM</small>
          </div>
        </div>

        <div className="org-switch">
          <span className="org-avatar">D</span>
          <div>
            <small>WORKSPACE</small>
            <b>Demo Organization</b>
          </div>
          <ChevronRight size={15} />
        </div>

        <div className="rail-label">OPERATIONS</div>

        <nav className="navigation">
          {nav.map(([name, Icon]) => (
            <button
              key={name}
              className={`nav-link ${tab === name ? 'selected' : ''}`}
              onClick={() => setTab(name)}
            >
              <Icon size={17} />
              <span>{name}</span>
              {name === 'Exceptions' && issues.length > 0 && (
                <em>{issues.length}</em>
              )}
              {tab === name && <i />}
            </button>
          ))}
        </nav>

        <div className="rail-foot">
          <div className="secure-mark">
            <ShieldCheck size={16} />
            <span>Audit trail active</span>
          </div>
          <small>HIRE FLOW / BUILD 01.26</small>
        </div>
      </aside>

      <main className="workspace-main">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>HIRE FLOW</span>
            <b>/</b>
            <span>{tab.toUpperCase()}</span>
          </div>

          <div className="top-actions">
            <span className="system-state"><i /> All systems operational</span>
            <button className="refresh-btn" onClick={load}>
              <RefreshCw size={14} className={busy ? 'spin' : ''} />
              {busy ? 'Syncing' : 'Sync data'}
            </button>
            <div className="profile-chip">EB</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <div className="section-kicker">
              <span className="kicker-line" /> RECRUITMENT OPERATIONS
            </div>
            <h1>{pageTitle}<span>.</span></h1>
            <p>
              One clear view of the people, processes and decisions
              moving your team forward.
            </p>
          </div>
          <div className="date-stamp">
            <small>WORKSPACE SNAPSHOT</small>
            <b>LIVE DATASET <i /></b>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={16} />
            {error}
            <button onClick={load}>Retry</button>
          </div>
        )}

        {tab === 'Overview' && (
          <>
            <section className="stat-grid">
              {stats.map(({ label, value, icon: Icon, note, tone }, index) => (
                <article className={`stat-card stat-${tone}`} key={label}>
                  <div className="stat-card-head">
                    <span className="stat-index">0{index + 1} / 04</span>
                    <Icon size={19} />
                  </div>
                  <strong>{value}</strong>
                  <div className="stat-label">{label}</div>
                  <small>{note}</small>
                </article>
              ))}
            </section>

            <section className="overview-grid">
              <article className="surface funnel-surface">
                <div className="surface-heading">
                  <div>
                    <span className="eyebrow">PIPELINE HEALTH / 01</span>
                    <h2>Hiring funnel</h2>
                    <p>Application volume by current lifecycle stage</p>
                  </div>
                  <span className="live-tag"><i /> LIVE</span>
                </div>

                <div className="funnel-list">
                  {Object.entries(data?.stage_distribution ?? {}).length
                    ? Object.entries(data!.stage_distribution).map(([stage, count]) => {
                        const percent = Math.max(
                          2,
                          count / Math.max(1, data!.applications) * 100
                        );

                        return (
                          <div className="funnel-item" key={stage}>
                            <span className="funnel-stage">
                              {stage.replaceAll('_', ' ')}
                            </span>
                            <div className="funnel-track">
                              <i style={{ width: `${percent}%` }} />
                            </div>
                            <b>{count.toLocaleString('en-IN')}</b>
                          </div>
                        );
                      })
                    : <div className="empty-state">No application data yet.</div>
                  }
                </div>

                <div className="funnel-foot">
                  <span><i /> APPLICATIONS IN PIPELINE</span>
                  <b>{(data?.applications ?? 0).toLocaleString('en-IN')}</b>
                </div>
              </article>

              <article className="surface quality-surface">
                <div className="surface-heading">
                  <div>
                    <span className="eyebrow">CONTROL ROOM / 02</span>
                    <h2>Data quality watch</h2>
                    <p>Exceptions requiring operational attention</p>
                  </div>
                  <button className="arrow-link" onClick={() => setTab('Exceptions')}>
                    Open register <ArrowUpRight size={15} />
                  </button>
                </div>

                <div className="quality-total">
                  <strong>{data?.open_issues ?? issues.length}</strong>
                  <span>open exceptions <b>·</b> {issues.length} recorded</span>
                </div>

                <div className="issue-preview">
                  {issues.slice(0, 4).map(issue => (
                    <div className="issue-line" key={issue.id}>
                      <span className="issue-symbol">
                        <AlertTriangle size={14} />
                      </span>
                      <div>
                        <b>{issue.issue_type.replaceAll('_', ' ')}</b>
                        <small>{issue.entity_id}</small>
                      </div>
                      <span className="priority">{issue.severity}</span>
                    </div>
                  ))}
                  {!issues.length && (
                    <div className="empty-state">
                      No exceptions currently recorded.
                    </div>
                  )}
                </div>

                <button className="scan-cta" onClick={scan}>
                  <ScanLine size={16} />
                  Run data quality scan <span>↗</span>
                </button>
              </article>
            </section>

            <section className="metric-band">
              <div className="metric-intro">
                <span className="eyebrow">PERFORMANCE INDICATORS / 03</span>
                <h2>Pipeline signals</h2>
              </div>
              <Metric
                label="Offer acceptance"
                value={`${data?.offer_acceptance_rate ?? 0}%`}
                detail="Accepted offers"
              />
              <Metric
                label="Screening pass rate"
                value={`${data?.screening_pass_rate ?? 0}%`}
                detail="Applications passing"
              />
              <Metric
                label="Feedback completeness"
                value={`${data?.feedback_completeness_rate ?? 0}%`}
                detail="Interview feedback"
              />
            </section>

            <section className="surface table-surface">
              <div className="surface-heading">
                <div>
                  <span className="eyebrow">LATEST ACTIVITY / 04</span>
                  <h2>Recent applications</h2>
                  <p>Candidate records moving through the hiring process</p>
                </div>
                <button className="arrow-link" onClick={() => setTab('Applications')}>
                  View all applications <ArrowUpRight size={15} />
                </button>
              </div>
              <ApplicationTable
                rows={visible.slice(0, 7)}
                onScore={scoreApplication}
              />
            </section>
          </>
        )}

        {tab === 'Applications' && (
          <section className="surface table-surface page-surface">
            <div className="surface-heading">
              <div>
                <span className="eyebrow">TALENT DATABASE / 01</span>
                <h2>Application register</h2>
                <p>Candidate-level status and explainable screening outcomes</p>
              </div>
              <SearchBox value={search} onChange={setSearch} />
            </div>
            <ApplicationTable rows={visible} onScore={scoreApplication} />
          </section>
        )}

        {tab === 'Exceptions' && (
          <section className="surface table-surface page-surface">
            <div className="surface-heading">
              <div>
                <span className="eyebrow">RISK & COMPLIANCE / 01</span>
                <h2>Exception register</h2>
                <p>
                  Every exception is recorded without silently changing source records.
                </p>
              </div>
              <button className="scan-cta small-cta" onClick={scan}>
                <ScanLine size={15} /> Run scan
              </button>
            </div>

            {issues.length
              ? (
                <div className="exception-list">
                  {issues.map(issue => (
                    <div className="exception-record" key={issue.id}>
                      <div className="exception-icon">
                        <AlertTriangle size={17} />
                      </div>
                      <div className="exception-copy">
                        <b>{issue.issue_type.replaceAll('_', ' ')}</b>
                        <p>{issue.description}</p>
                        <small>
                          {issue.entity_type} <span>·</span> {issue.entity_id}
                        </small>
                      </div>
                      <span className={`record-status ${issue.resolved ? 'resolved' : ''}`}>
                        {issue.resolved ? 'Resolved' : issue.severity}
                      </span>
                    </div>
                  ))}
                </div>
              )
              : <div className="empty-state">No exceptions found.</div>
            }
          </section>
        )}

        {tab === 'Requisitions' && (
          <section className="surface table-surface page-surface">
            <div className="surface-heading">
              <div>
                <span className="eyebrow">ROLE MANAGEMENT / 01</span>
                <h2>Requisition register</h2>
                <p>Approved and closed roles with compensation bands</p>
              </div>
              <span className="count-tag">{reqs.length} ROLES</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Requisition</th>
                    <th>Role</th>
                    <th>Department</th>
                    <th>Salary band (INR)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {reqs.map(r => (
                    <tr key={r.id}>
                      <td className="mono">{r.requisition_id}</td>
                      <td><b>{r.title}</b></td>
                      <td>{r.department}</td>
                      <td>{money(r.salary_min)} – {money(r.salary_max)}</td>
                      <td><Status value={r.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === 'Interviews' && (
          <section className="surface table-surface page-surface">
            <div className="surface-heading">
              <div>
                <span className="eyebrow">SCHEDULING / 01</span>
                <h2>Interview schedule</h2>
                <p>Scheduled rounds and interviewer assignments</p>
              </div>
              <span className="count-tag">{interviews.length} ROUNDS</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Interview</th>
                    <th>Application PK</th>
                    <th>Interviewer PK</th>
                    <th>Round</th>
                    <th>Scheduled at</th>
                    <th>Availability</th>
                  </tr>
                </thead>
                <tbody>
                  {interviews.slice(0, 250).map(i => (
                    <tr key={i.id}>
                      <td className="mono">{i.interview_id}</td>
                      <td>{i.application_id}</td>
                      <td>{i.interviewer_id}</td>
                      <td>{i.round_name}</td>
                      <td>{new Date(i.scheduled_at).toLocaleString()}</td>
                      <td>
                        <Status value={i.interviewer_available ? 'available' : 'conflict'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === 'Offers' && (
          <section className="surface table-surface page-surface">
            <div className="surface-heading">
              <div>
                <span className="eyebrow">COMPENSATION / 01</span>
                <h2>Offer register</h2>
                <p>Approved compensation and candidate decisions</p>
              </div>
              <span className="count-tag">{offers.length} OFFERS</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Offer</th>
                    <th>Application PK</th>
                    <th>Salary</th>
                    <th>Approver</th>
                    <th>Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {offers.map(o => (
                    <tr key={o.id}>
                      <td className="mono">{o.offer_id}</td>
                      <td>{o.application_id}</td>
                      <td>{money(o.salary)}</td>
                      <td>{o.approved_by ?? '—'}</td>
                      <td><Status value={o.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <footer className="page-footer">
          <span>HIRE FLOW INTELLIGENCE <b>©</b> 2026</span>
          <span>
            <ShieldCheck size={13} />
            Synthetic candidate data · Audit-aware workflows
          </span>
        </footer>
      </main>

      {/* Screening result modal */}
      {screeningResult && (
        <div
          className="screening-overlay"
          onClick={() => setScreeningResult(null)}
        >
          <div
            className="screening-modal"
            onClick={e => e.stopPropagation()}
          >
            <div className="modal-topline">
              <span className="eyebrow">HIRE FLOW / SCREENING REPORT</span>
              <button
                className="modal-close"
                onClick={() => setScreeningResult(null)}
              >
                ×
              </button>
            </div>

            <div className="modal-title">
              <div>
                <span className="eyebrow">CANDIDATE EVALUATION</span>
                <h2>Screening complete<span>.</span></h2>
                <p>
                  Automated assessment against the requisition requirements.
                </p>
              </div>

              <span className={`decision-badge ${screeningResult.decision.toLowerCase()}`}>
                {screeningResult.decision.toUpperCase()}
              </span>
            </div>

            <div className="score-panel">
              <div>
                <small>OVERALL SCREENING SCORE</small>
                <div className="score-number">
                  {Number(screeningResult.score).toFixed(1)}
                  <span>/100</span>
                </div>
              </div>

              <div className="score-ring">
                <svg viewBox="0 0 100 100">
                  <circle className="ring-track" cx="50" cy="50" r="42" />
                  <circle
                    className="ring-progress"
                    cx="50"
                    cy="50"
                    r="42"
                    style={{
                      strokeDasharray: `${
                        Math.min(100, Math.max(0, screeningResult.score)) * 2.64
                      } 264`
                    }}
                  />
                </svg>
                <span>{Math.round(screeningResult.score)}%</span>
              </div>
            </div>

            <div className="modal-metrics">
              <div className="modal-metric">
                <span>Skill match</span>
                <strong>{screeningResult.skill_match}%</strong>
                <div className="metric-track">
                  <i style={{
                    width: `${Math.min(100, screeningResult.skill_match)}%`
                  }} />
                </div>
              </div>

              <div className="modal-metric">
                <span>Experience score</span>
                <strong>{screeningResult.experience_score}</strong>
                <div className="metric-track">
                  <i style={{
                    width: `${
                      Math.min(100, Math.max(0, screeningResult.experience_score))
                    }%`
                  }} />
                </div>
              </div>
            </div>

            <div className="skills-result">
              <div>
                <span className="eyebrow">REQUIRED SKILLS</span>
                <strong>
                  {screeningResult.matched_skills}/
                  {screeningResult.required_skills}
                </strong>
              </div>
              <span className="skills-success">
                <ShieldCheck size={16} />
                {screeningResult.matched_skills === screeningResult.required_skills
                  ? 'All required skills matched'
                  : 'Some required skills missing'}
              </span>
            </div>

            <div className="threshold-note">
              <span>PASS THRESHOLD</span>
              <strong>{screeningResult.threshold}/100</strong>
            </div>

            <div className="modal-footer">
              <span>
                <ShieldCheck size={14} />
                Explainable screening result
              </span>
              <button onClick={() => setScreeningResult(null)}>
                Done <ArrowUpRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  detail
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="metric-cell">
      <small>{label}</small>
      <strong>{value}</strong>
      <span>{detail}</span>
    </div>
  );
}

function Status({ value }: { value: string }) {
  const good = [
    'hired', 'offer', 'available', 'approved', 'resolved'
  ].includes(value.toLowerCase());

  return (
    <span className={`status-pill ${good ? 'good' : ''}`}>
      {value.replaceAll('_', ' ')}
    </span>
  );
}

function SearchBox({
  value,
  onChange
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="search-box">
      <Search size={15} />
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Find a candidate or role"
      />
      <kbd>⌘ K</kbd>
    </label>
  );
}

function ApplicationTable({
  rows,
  onScore
}: {
  rows: Application[];
  onScore: (id: number) => void;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Candidate</th>
            <th>Application ID</th>
            <th>Requisition</th>
            <th>Screening score</th>
            <th>Current stage</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(a => (
            <tr key={a.id}>
              <td>
                <b>{a.candidate}</b>
                <small>{a.candidate_id}</small>
              </td>
              <td className="mono">{a.application_id}</td>
              <td>{a.requisition}</td>
              <td>
                {a.screening_score === null
                  ? <span className="muted">Not scored</span>
                  : (
                    <span className="score-value">
                      {a.screening_score}<small>/100</small>
                    </span>
                  )
                }
              </td>
              <td><Status value={a.stage} /></td>
              <td>
                <button
                  className="evaluate-btn"
                  onClick={() => onScore(a.id)}
                >
                  Evaluate <ArrowUpRight size={12} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {!rows.length && (
        <div className="empty-state">
          No matching records. Try another search.
        </div>
      )}
    </div>
  );
}
