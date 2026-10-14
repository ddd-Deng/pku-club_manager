/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 'true' 时使用本地 mock，'false' 时请求真实后端 */
  readonly VITE_USE_MOCK: string
  /** 后端服务 baseURL，真实模式下生效 */
  readonly VITE_API_BASE_URL: string
  /** 应用标题 */
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
