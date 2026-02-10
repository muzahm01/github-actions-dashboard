/**
 * Repository-related type definitions
 */

export interface Repository {
  id: number
  github_id: number
  name: string
  full_name: string
  owner: string
  description: string | null
  default_branch: string
  is_active: boolean
  webhook_configured: boolean
  last_synced_at: string | null
  created_at: string
  updated_at: string
}
