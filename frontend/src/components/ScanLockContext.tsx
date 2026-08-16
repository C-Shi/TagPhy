import { createContext, useContext } from "react"

type ScanLockContextValue = {
  scanLocked: boolean
  setScanLocked: (locked: boolean) => void
}

export const ScanLockContext = createContext<ScanLockContextValue>({
  scanLocked: false,
  setScanLocked: () => {},
})

export function useScanLock() {
  return useContext(ScanLockContext)
}
