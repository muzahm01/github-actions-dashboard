/**
 * Type definitions for GitHub Actions Dashboard
 *
 * Re-exports all types from domain-specific modules for backward compatibility.
 * Prefer importing from specific modules for new code:
 *   import type { Repository } from '@/types/repository'
 */

export type { Repository } from './repository'
export type { Workflow, WorkflowRun, WorkflowRunStatus, WorkflowRunConclusion } from './workflow'
export type { Job, JobStep, JobConclusion } from './job'
export type { Log, TestResult, ErrorAnalysis } from './analysis'
export type { DashboardStats, PaginatedResponse } from './dashboard'
export type { SearchResult, SearchResultMetadata } from './search'
