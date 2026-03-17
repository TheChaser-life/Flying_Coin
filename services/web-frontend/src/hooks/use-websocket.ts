"use client"

import { useEffect, useRef, useState, useCallback } from "react"

export function useWebSocket(url: string | null) {
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [readyState, setReadyState] = useState<number>(0) // 0: connecting, 1: open, 2: closing, 3: closed
  const ws = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (!url) return

    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setReadyState(1)
      console.log("WebSocket connected to:", url)
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
      } catch (e) {
        setLastMessage(event.data)
      }
    }

    ws.current.onclose = () => {
      setReadyState(3)
      console.log("WebSocket disconnected")
      // Simple reconnection logic
      setTimeout(connect, 3000)
    }

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error)
      ws.current?.close()
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      ws.current?.close()
    }
  }, [connect])

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }, [])

  return { lastMessage, readyState, sendMessage }
}
