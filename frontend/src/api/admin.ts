import { request } from './request'
import type {
  AdminAccount,
  AdminAccountQuery,
  AdminClub,
  AssignPresidentPayload,
  EditAccountPayload
} from '@/types/admin'
import type { PageQuery, PageResult } from '@/types/common'

export function getAccounts(params: AdminAccountQuery): Promise<PageResult<AdminAccount>> {
  return request({ method: 'GET', url: '/api/admin/users', params: { ...params } })
}

export function editAccount(id: string, data: EditAccountPayload): Promise<AdminAccount> {
  return request({ method: 'PUT', url: `/api/admin/users/${id}`, data })
}

export function setAccountStatus(id: string, isActive: boolean): Promise<AdminAccount> {
  return request({ method: 'PUT', url: `/api/admin/users/${id}/status`, data: { isActive } })
}

export function getAdminClubs(
  params: PageQuery & { keyword?: string }
): Promise<PageResult<AdminClub>> {
  return request({ method: 'GET', url: '/api/admin/clubs', params: { ...params } })
}

export function assignPresident(id: string, data: AssignPresidentPayload): Promise<AdminClub> {
  return request({ method: 'PUT', url: `/api/admin/clubs/${id}/president`, data })
}
