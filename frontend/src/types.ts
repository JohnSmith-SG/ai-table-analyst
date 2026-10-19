export type Cell = string | number | null
export type ColStats = { count: number; mean: number; min: number; max: number; sum: number }
export type TableData = {
  filename: string
  columns: string[]
  rows: Cell[][]
  total_rows: number
  stats: Record<string, ColStats>
}
export type Provider = 'yandex' | 'gigachat'
export type Analysis = { analysis: string; model: string; seconds: number; provider: Provider }
