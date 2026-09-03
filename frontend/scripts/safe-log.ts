export function sanitizeDevMessage(message: string): string {
  return message.replace(/(\/api\/internal\/v1\/[^\s?]*)\?[^\s]*/g, '$1?[redacted]');
}
