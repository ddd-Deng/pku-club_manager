import type { PageResult } from '@/types/common'
import type {
  CreateReservationPayload,
  ReservationQuery,
  ReviewReservationPayload,
  Venue,
  VenueReservation
} from '@/types/venue'

import { request } from './request'

/** 场地与可预约时段 */
export function getVenues(): Promise<Venue[]> {
  return request<Venue[]>({ method: 'GET', url: '/api/venues' })
}

/** 提交场地 / 物资预约（社长 / 管理员） */
export function createReservation(payload: CreateReservationPayload): Promise<VenueReservation> {
  return request<VenueReservation>({
    method: 'POST',
    url: '/api/venue-reservations',
    data: payload
  })
}

/** 预约单列表（社长看本社团，管理员看全部） */
export function getReservations(
  query: ReservationQuery = {}
): Promise<PageResult<VenueReservation>> {
  return request<PageResult<VenueReservation>>({
    method: 'GET',
    url: '/api/venue-reservations',
    params: { ...query }
  })
}

/** 审批预约单（管理员） */
export function reviewReservation(
  id: string,
  payload: ReviewReservationPayload
): Promise<VenueReservation> {
  return request<VenueReservation>({
    method: 'PUT',
    url: `/api/venue-reservations/${id}`,
    data: payload
  })
}
