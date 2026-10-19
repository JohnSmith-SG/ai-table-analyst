import { useState } from 'react'
import FileUpload from './components/FileUpload'
import DataTable from './components/DataTable'
import DataChart from './components/DataChart'
import AnalysisBlock from './components/AnalysisBlock'
import type { Analysis, Provider, TableData } from './types'

const N_ROWS = 15

export default function App() {
  const [data, setData] = useState<TableData | null>(null)
  const [provider, setProvider] = useState<Provider>('yandex')
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const upload = async (file: File) => {
    setLoading(true)
    setError('')
    setAnalysis(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await fetch('/api/upload', { method: 'POST', body: fd })
      const j = await r.json()
      if (!r.ok) throw new Error(j.error || 'Ошибка загрузки')
      setData(j)
    } catch (e) {
      setData(null)
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setLoading(false)
    }
  }

  const analyze = async () => {
    if (!data) return
    setBusy(true)
    setError('')
    try {
      const r = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, columns: data.columns, rows: data.rows.slice(0, N_ROWS) }),
      })
      const j = await r.json()
      if (!r.ok) throw new Error(j.error || 'Ошибка анализа')
      setAnalysis(j)
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setBusy(false)
    }
  }

  const report = async () => {
    if (!data || !analysis) return
    const r = await fetch('/api/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: data.filename,
        columns: data.columns,
        rows: data.rows.slice(0, N_ROWS),
        total_rows: data.total_rows,
        stats: data.stats,
        analysis: analysis.analysis,
        model: analysis.model,
        seconds: analysis.seconds,
      }),
    })
    if (!r.ok) return setError('Не удалось собрать PDF')
    const url = URL.createObjectURL(await r.blob())
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${analysis.provider}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main>
      <h1>ИИ-аналитик таблиц</h1>
      <FileUpload onFile={upload} loading={loading} />
      {!data && error && <p className="error">{error}</p>}
      {data && (
        <>
          <p>
            Файл <b>{data.filename}</b>: {data.total_rows} строк, {data.columns.length} колонок
          </p>
          <section className="card">
            <h2>Данные</h2>
            <DataTable data={data} highlight={N_ROWS} />
          </section>
          <section className="card">
            <h2>График</h2>
            <DataChart data={data} />
          </section>
          <AnalysisBlock
            provider={provider}
            onProvider={setProvider}
            analysis={analysis}
            busy={busy}
            error={error}
            onAnalyze={analyze}
            onReport={report}
          />
        </>
      )}
    </main>
  )
}
