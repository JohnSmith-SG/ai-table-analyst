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

// облачные модели отвечают за секунды, локальная на CPU — за минуты
function formatSeconds(s: number) {
  if (s < 120) return `${s} с`
  const m = Math.floor(s / 60)
  return m < 60 ? `${m} мин ${Math.round(s % 60)} с` : `${Math.floor(m / 60)} ч ${m % 60} мин`
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
          <button className={provider === 'local' ? 'on' : ''} onClick={() => onProvider('local')}>
            Gemma3 (локально)
          </button>
          <button className={provider === 'local-qwen' ? 'on' : ''} onClick={() => onProvider('local-qwen')}>
            Qwen3 (локально)
          </button>
        </div>
        <button className="primary" onClick={onAnalyze} disabled={busy}>
          {busy ? 'Нейросеть думает…' : 'Проанализировать данные'}
        </button>
        <button onClick={onReport} disabled={!analysis}>
          Скачать PDF-отчёт
        </button>
      </div>
      {busy && provider.startsWith('local') && (
        <p className="hint">Модель работает на этом компьютере без видеокарты — ответ может идти от минут до часов.</p>
      )}
      {error && <p className="error">{error}</p>}
      {analysis && (
        <>
          <p className="hint">
            {analysis.model} · ответ за {formatSeconds(analysis.seconds)}
          </p>
          <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
        </>
      )}
    </section>
  )
}
