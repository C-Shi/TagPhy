import type { Picture } from '../api/types'
import { PreviewItem } from './PreviewItem'

type Props = {
  pictures: Picture[]
}

export function Preview({ pictures }: Props) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-auto bg-canvas/40 px-4 py-4 library:px-6">
      <h2 className="text-lg font-semibold text-ink">Preview</h2>
      {pictures.length === 0 ? (
        <div className="mt-6 flex flex-1 flex-col items-center justify-center rounded-md border border-dashed border-line bg-surface px-4 py-12 text-center">
          <p className="text-base font-semibold text-ink">No photos</p>
          <p className="mt-1 text-sm text-ink-muted">
            Scan photos or clear filters to see previews here.
          </p>
        </div>
      ) : (
        <div className="mt-4 flex flex-wrap content-start gap-3">
          {pictures.map((picture) => (
            <PreviewItem key={picture.id} picture={picture} />
          ))}
        </div>
      )}
    </div>
  )
}
