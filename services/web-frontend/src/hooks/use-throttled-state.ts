"use client"

import { useEffect, useRef, useState } from "react"

/**
 * Hook để throttle việc cập nhật state.
 * Giúp giảm số lần re-render khi giá trị đầu vào thay đổi quá nhanh (ví dụ: từ WebSocket).
 */
export function useThrottledState<T>(initialValue: T, delay: number = 500) {
  const [state, setState] = useState<T>(initialValue)
  const lastUpdateRef = useRef<number>(0)
  const pendingValueRef = useRef<T | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const setThrottledState = (newValue: T) => {
    const now = Date.now()
    const timeSinceLastUpdate = now - lastUpdateRef.current

    if (timeSinceLastUpdate >= delay) {
      // Đã đủ thời gian, cập nhật ngay lập tức
      setState(newValue)
      lastUpdateRef.current = now
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    } else {
      // Lưu lại giá trị chờ và đặt hẹn giờ cập nhật
      pendingValueRef.current = newValue
      if (!timeoutRef.current) {
        timeoutRef.current = setTimeout(() => {
          if (pendingValueRef.current !== null) {
            setState(pendingValueRef.current)
            lastUpdateRef.current = Date.now()
            pendingValueRef.current = null
            timeoutRef.current = null
          }
        }, delay - timeSinceLastUpdate)
      }
    }
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  return [state, setThrottledState] as const
}
