import { FiAlertTriangle, FiCheckCircle, FiXCircle } from 'react-icons/fi'
import type { ConnectionStatus } from '../types'

export const getConnectionStatus = (liveDelta: number): ConnectionStatus => {
  if (liveDelta === Infinity) return { color: 'gray', label: '未接続', icon: FiXCircle }
  if (liveDelta < 5000) return { color: 'green', label: '安定', icon: FiCheckCircle }
  if (liveDelta < 15000) return { color: 'yellow', label: '遅延', icon: FiAlertTriangle }
  return { color: 'red', label: '切断', icon: FiXCircle }
}

export const getLiveColor = (liveDelta: number): 'gray' | 'green' | 'yellow' | 'red' => {
  if (liveDelta === Infinity) return 'gray'
  if (liveDelta < 5000) return 'green'
  if (liveDelta < 15000) return 'yellow'
  return 'red'
}


