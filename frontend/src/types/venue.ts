import type { PageQuery } from './common'

/** 场地可预约时段 */
export interface VenueSlot {
  date: string
  timeSlot: string
  available: boolean
}

/** 场地 */
export interface Venue {
  id: string
  name: string
  location: string
  slots: VenueSlot[]
}

export type ReservationStatus = 'pending' | 'approved' | 'rejected'

/** 场地 / 物资预约单 */
export interface VenueReservation {
  id: string
  venueId: string
  venueName: string
  clubId: string
  clubName: string
  date: string
  timeSlot: string
  purpose: string
  /** 随场地一起预约的物资 */
  items: string[]
  status: ReservationStatus
  createdAt: string
}

export interface CreateReservationPayload {
  venueId: string
  date: string
  timeSlot: string
  purpose: string
  items?: string[]
}

export interface ReviewReservationPayload {
  action: 'approve' | 'reject'
  comment?: string
}

export interface ReservationQuery extends PageQuery {
  clubId?: string
  status?: ReservationStatus
}
