import { TOKEN_STORAGE_KEY } from './constants'

/** 读取登录 token */
export function getToken(): string {
  return localStorage.getItem(TOKEN_STORAGE_KEY) ?? ''
}

/** 写入登录 token */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

/** 清除登录 token */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}
