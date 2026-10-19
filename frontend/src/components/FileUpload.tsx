type Props = { onFile: (f: File) => void; loading: boolean }

export default function FileUpload({ onFile, loading }: Props) {
  return (
    <label className="upload">
      <input
        type="file"
        accept=".csv,.xlsx,.xls,.pdf"
        disabled={loading}
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
          e.target.value = ''
        }}
      />
      <span>{loading ? 'Загрузка…' : 'Выберите файл таблицы (CSV, XLSX или PDF)'}</span>
    </label>
  )
}
