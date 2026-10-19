import type { TableData } from '../types'

export default function DataTable({ data, highlight = 15 }: { data: TableData; highlight?: number }) {
  return (
    <div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {data.columns.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={i} className={i < highlight ? 'sent' : ''}>
                {r.map((v, j) => (
                  <td key={j}>{v ?? ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hint">Строки, выделенные цветом, — первые {highlight}: именно они уходят в нейросеть.</p>
    </div>
  )
}
