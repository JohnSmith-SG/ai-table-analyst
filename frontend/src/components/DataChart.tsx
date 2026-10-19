import { useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { TableData } from '../types'

export default function DataChart({ data }: { data: TableData }) {
  const numeric = Object.keys(data.stats)
  const [col, setCol] = useState(numeric[0] ?? '')
  const rows = useMemo(() => {
    const idx = data.columns.indexOf(col)
    // подпись: все нечисловые колонки через пробел, например «2024-01 Западная Сибирь»
    const labelIdx = data.columns.map((c, i) => (data.stats[c] ? -1 : i)).filter((i) => i >= 0)
    return data.rows.map((r, i) => ({
      name: labelIdx.map((k) => r[k]).join(' ') || String(i + 1),
      value: typeof r[idx] === 'number' ? (r[idx] as number) : 0,
    }))
  }, [data, col])

  if (!numeric.length) return <p className="hint">В таблице нет числовых колонок для графика.</p>
  return (
    <div>
      <label>
        Колонка:{' '}
        <select value={col} onChange={(e) => setCol(e.target.value)}>
          {numeric.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>
      <div style={{ width: '100%', height: 300, marginTop: 8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" hide />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" name={col} fill="#2f6fdb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
