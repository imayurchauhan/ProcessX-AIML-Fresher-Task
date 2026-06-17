import { useMemo, useState } from 'react'

type Issue = {
  day: string
  flag_type: string
  requirement: string
  explanation: string
  evidence: string
}

type ResidentResult = {
  resident: string
  issues: Issue[]
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<ResidentResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [engine, setEngine] = useState<string | null>(null)

  const issueCount = useMemo(
    () => results.reduce((total, resident) => total + resident.issues.length, 0),
    [results],
  )

  async function analyzeWorkbook() {
    if (!file) {
      setError('Select a workbook first.')
      return
    }

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const payload = await response.json()
      const residents: ResidentResult[] = Object.entries(payload.issues_by_resident ?? {}).map(([resident, issues]) => ({
        resident,
        issues: issues as Issue[],
      }))
      setResults(residents)
      setEngine(payload.engine ?? null)
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : 'Analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  async function downloadWorkbook() {
    if (!file) {
      setError('Select a workbook first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/generate-output', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'ProcessX_Output.xlsx'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : 'Download failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">ProcessX AIML Interview Task</p>
          <h1>Falls management compliance, built to be explainable.</h1>
          <p className="lede">
            Upload a resident workbook, evaluate the daily notes against the structured policy rules, and export a completed output sheet with only non-complete findings.
          </p>

          <div className="stats">
            <div className="stat-card">
              <span>Evaluation mode</span>
              <strong>{engine === 'groq-llm' ? '🤖 Groq LLM' : engine === 'rule-based' ? '📋 Rule-based' : 'Rule-first, LLM-ready'}</strong>
            </div>
            <div className="stat-card">
              <span>Supported outputs</span>
              <strong>Missing / Incomplete / Vague</strong>
            </div>
            <div className="stat-card">
              <span>Workbook output</span>
              <strong>Excel + JSON</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          {engine && (
            <div className={`engine-badge ${engine === 'groq-llm' ? 'engine-llm' : 'engine-rules'}`}>
              <span className="engine-dot" />
              {engine === 'groq-llm' ? '🤖 Powered by Groq LLM (llama-3.3-70b)' : '📋 Rule-based engine (no API key)'}
            </div>
          )}
          <div className="upload-zone">
            <label className="upload-label" htmlFor="workbook">
              {file ? file.name : 'Choose a workbook to analyze'}
            </label>
            <input
              id="workbook"
              type="file"
              accept=".xlsx"
              onChange={(event) => {
                const selectedFile = event.target.files?.[0] ?? null
                setFile(selectedFile)
                setError(null)
              }}
            />
            <p className="upload-hint">Use the ProcessX workbook with paired Input and Output sheets.</p>
          </div>

          <div className="actions">
            <button type="button" onClick={analyzeWorkbook} disabled={loading} className="primary">
              {loading ? 'Working…' : 'Analyze workbook'}
            </button>
            <button type="button" onClick={downloadWorkbook} disabled={loading} className="secondary">
              Download completed Excel
            </button>
          </div>

          <div className="summary-strip">
            <div>
              <span>Residents processed</span>
              <strong>{results.length}</strong>
            </div>
            <div>
              <span>Total issues</span>
              <strong>{issueCount}</strong>
            </div>
          </div>

          {error ? <div className="error-box">{error}</div> : null}
        </div>
      </section>

      <section className="results">
        <div className="section-heading">
          <p>Compliance findings</p>
          <h2>Every flag is traceable back to the note text.</h2>
          {engine && (
            <div className={`engine-badge inline-badge ${engine === 'groq-llm' ? 'engine-llm' : 'engine-rules'}`}>
              <span className="engine-dot" />
              {engine === 'groq-llm' ? '🤖 Groq LLM' : '📋 Rule-based'}
            </div>
          )}
        </div>

        <div className="result-grid">
          {results.length === 0 ? (
            <article className="empty-state">
              <h3>No analysis yet</h3>
              <p>Upload a workbook to inspect the issues grouped by resident.</p>
            </article>
          ) : issueCount === 0 ? (
            <article className="empty-state compliant">
              <h3>✅ Fully Compliant</h3>
              <p>No issues found across all {results.length} resident{results.length !== 1 ? 's' : ''}. All notes meet the policy requirements.</p>
            </article>
          ) : (
            results.map((resident) => (
              <article className="resident-card" key={resident.resident}>
                <header>
                  <h3>{resident.resident}</h3>
                  <span>{resident.issues.length} issues</span>
                </header>

                {resident.issues.length === 0 ? (
                  <div className="clean-pill">No issues found</div>
                ) : (
                  <div className="issue-list">
                    {resident.issues.map((issue, index) => (
                      <div className="issue-item" key={`${issue.day}-${issue.requirement}-${index}`}>
                        <div className="issue-meta">
                          <strong>{issue.day}</strong>
                          <span>{issue.flag_type}</span>
                        </div>
                        <h4>{issue.requirement}</h4>
                        <p>{issue.explanation}</p>
                        {issue.evidence ? <code>{issue.evidence}</code> : null}
                      </div>
                    ))}
                  </div>
                )}
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  )
}

export default App