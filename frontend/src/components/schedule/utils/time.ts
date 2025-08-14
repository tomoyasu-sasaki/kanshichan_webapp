export const timeToMinutes = (timeStr: string): number => {
  const [hh, mm] = timeStr.split(':').map(Number)
  if (Number.isNaN(hh) || Number.isNaN(mm)) return Number.MAX_SAFE_INTEGER
  return hh * 60 + mm
}

export const minutesUntil = (timeStr: string, now: Date = new Date()): number => {
  const [hours, minutes] = timeStr.split(':').map(Number)
  const scheduleTime = new Date(now)
  scheduleTime.setHours(hours, minutes, 0, 0)
  const diff = Math.floor((scheduleTime.getTime() - now.getTime()) / (1000 * 60))
  return Math.max(0, diff)
}


