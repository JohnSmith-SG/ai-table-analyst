import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { Analysis, Provider } from '../types'

type Props = {
  provider: Provider
  onProvider: (p: Provider) => void
  analysis: Analysis | null
  busy: boolean
  error: string
  onAnalyze: () => void
  onReport: () => void
}

export default function AnalysisBlock({ provider, onProvider, analysis, busy, error, onAnalyze, onReport }: Props) {
  // Markdown ответа (**жирный**, списки, заголовки) превращаем в HTML и чистим от опасного кода
  const html = analysis ? DOMPurify.sanitize(marked.parse(analysis.analysis, { async: false }) as string) : ''
  return (
    <section className="card">
      <h2>Анализ от нейросети</h2>
      <div className="row">
        <div className="switch">
          <button className={provider === 'yandex' ? 'on' : ''} onClick={() => onProvider('yandex')}>
            YandexGPT
          </button>
          <button className={provider === 'gigachat' ? 'on' : ''} onClick={() => onProvider('gigachat')}>
            GigaChat
          </button>
        </div>
        <button className="primary" onClick={onAnalyze} disabled={busy}>
          {busy ? 'Нейросеть думает…' : 'Проанализировать данные'}
        </button>
        <button onClick={onReport} disabled={!analysis}>
          Скачать PDF-отчёт
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {analysis && (
        <>
          <p className="hint">
            {analysis.model} · ответ за {analysis.seconds} с
          </p>
          <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
        </>
      )}
    </section>
  )
}
