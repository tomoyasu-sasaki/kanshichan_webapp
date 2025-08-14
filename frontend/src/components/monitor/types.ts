import type { IconType } from 'react-icons'
import type { DetectionStatus as WsDetectionStatus } from '../../utils/websocket'

export type DetectionStatus = WsDetectionStatus

export interface ConnectionStatus {
  color: 'gray' | 'green' | 'yellow' | 'red'
  label: string
  icon: IconType
}


