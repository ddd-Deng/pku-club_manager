import type { PageQuery } from './common'
import type { UserInfo } from './user'

export interface AdminAccount extends UserInfo {
  isActive: boolean
  createdAt: string
}

export interface AdminAccountQuery extends PageQuery {
  keyword?: string
  role?: 'student' | 'clubAdmin'
  isActive?: boolean
}

export interface AdminClub {
  id: string
  name: string
  category: string
  president: { id: string; name: string; studentNo: string } | null
}

export interface AssignPresidentPayload {
  userId: string
  expectedPresidentId: string | null
}

export interface EditAccountPayload {
  name?: string
  email?: string
}
