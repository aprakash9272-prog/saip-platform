export interface Paginated<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface Vendor {
  id: number;
  name: string;
  website: string | null;
  description: string | null;
  headquarters: string | null;
  created_at: string;
  updated_at: string;
}

export interface VendorInput {
  name: string;
  website?: string | null;
  description?: string | null;
  headquarters?: string | null;
}

export interface Product {
  id: number;
  vendor_id: number;
  name: string;
  category: string | null;
  description: string | null;
  website: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductInput {
  name: string;
  vendor_id: number;
  category?: string | null;
  description?: string | null;
  website?: string | null;
}

export interface Edition {
  id: number;
  product_id: number;
  name: string;
  tier: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface EditionInput {
  name: string;
  product_id: number;
  tier?: string | null;
  description?: string | null;
}

export interface Module {
  id: number;
  edition_id: number;
  name: string;
  description: string | null;
  capability_ids: number[];
  created_at: string;
  updated_at: string;
}

export interface ModuleInput {
  name: string;
  edition_id: number;
  description?: string | null;
  capability_ids?: number[];
}

export interface Domain {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface DomainInput {
  name: string;
  description?: string | null;
}

export interface Capability {
  id: number;
  name: string;
  code: string;
  domain_id: number;
  description: string | null;
  risk_category: string | null;
  created_at: string;
  updated_at: string;
}

export interface CapabilityInput {
  name: string;
  code: string;
  domain_id: number;
  description?: string | null;
  risk_category?: string | null;
}

export interface CapabilityFacets {
  domains: Domain[];
  risk_categories: string[];
}

export interface CapabilityImportSummary {
  created: number;
  updated: number;
  unchanged: number;
}

export interface Framework {
  id: number;
  name: string;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface FrameworkInput {
  name: string;
  version: string;
}

export interface FrameworkMapping {
  id: number;
  capability_id: number;
  framework_id: number;
  control_id: string;
  control_name: string;
  created_at: string;
  updated_at: string;
}

export interface FrameworkMappingInput {
  capability_id: number;
  framework_id: number;
  control_id: string;
  control_name: string;
}

export const DEPLOYMENT_MODELS = ["Agent", "SaaS", "Network", "Hybrid"] as const;
export const AVAILABILITY_STATUSES = [
  "Generally Available",
  "Beta",
  "Preview",
  "Deprecated",
  "Discontinued",
] as const;
export const PLATFORMS = ["Windows", "macOS", "Linux", "Cloud", "Mobile"] as const;

export interface ProductCapabilityMapping {
  id: number;
  vendor_id: number;
  product_id: number;
  edition_id: number;
  module_id: number;
  capability_id: number;
  licensing_tier: string | null;
  supported_platforms: string[];
  deployment_model: string;
  availability_status: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCapabilityMappingInput {
  vendor_id: number;
  product_id: number;
  edition_id: number;
  module_id: number;
  capability_id: number;
  licensing_tier?: string | null;
  supported_platforms?: string[];
  deployment_model: string;
  availability_status?: string;
}

export interface ProductCapabilityMappingFacets {
  deployment_models: string[];
  availability_statuses: string[];
  licensing_tiers: string[];
}

export interface BulkOperationResult {
  updated: number;
  deleted: number;
  failed: string[];
}

// ------------------------------------------------- Customer Assessment Workspace --

export interface Customer {
  id: number;
  name: string;
  industry: string | null;
  description: string | null;
  website: string | null;
  headquarters: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerInput {
  name: string;
  industry?: string | null;
  description?: string | null;
  website?: string | null;
  headquarters?: string | null;
}

export interface BusinessUnit {
  id: number;
  customer_id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessUnitInput {
  name: string;
  customer_id: number;
  description?: string | null;
}

export const ENVIRONMENT_TYPES = [
  "Production",
  "UAT",
  "Development",
  "DR",
  "OT",
] as const;

export interface Environment {
  id: number;
  customer_id: number;
  name: string;
  environment_type: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentInput {
  name: string;
  customer_id: number;
  environment_type: string;
  description?: string | null;
}

export const ASSESSMENT_STATUSES = [
  "Draft",
  "In Progress",
  "Completed",
  "Archived",
] as const;

export interface AssessmentProject {
  id: number;
  customer_id: number;
  name: string;
  description: string | null;
  status: string;
  start_date: string | null;
  target_completion_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssessmentProjectInput {
  name: string;
  customer_id: number;
  description?: string | null;
  status?: string;
  start_date?: string | null;
  target_completion_date?: string | null;
}

export const DEPLOYMENT_STATUSES = [
  "Not Started",
  "In Progress",
  "Deployed",
  "Decommissioned",
] as const;

export interface ProductAssignment {
  id: number;
  assessment_project_id: number;
  vendor_id: number;
  product_id: number;
  edition_id: number;
  environment_id: number;
  module_ids: number[];
  license_quantity: number | null;
  deployment_model: string;
  deployment_status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductAssignmentInput {
  assessment_project_id: number;
  vendor_id: number;
  product_id: number;
  edition_id: number;
  environment_id: number;
  module_ids?: number[];
  license_quantity?: number | null;
  deployment_model: string;
  deployment_status?: string;
  notes?: string | null;
}

export interface RefItem {
  id: number;
  name: string;
}

export interface CapabilityRefItem {
  id: number;
  code: string;
  name: string;
}

export interface FrameworkRefItem {
  id: number;
  name: string;
  version: string;
}

export interface AssessmentDashboard {
  total_deployed_products: number;
  distinct_product_count: number;
  vendor_count: number;
  vendors: RefItem[];
  module_count: number;
  modules: RefItem[];
  capability_count: number;
  capabilities: CapabilityRefItem[];
  domain_count: number;
  domains: RefItem[];
  framework_count: number;
  frameworks: FrameworkRefItem[];
}

export interface ProductAssignmentExport {
  vendor: string;
  product: string;
  edition: string;
  modules: string[];
  environment: string;
  license_quantity: number | null;
  deployment_model: string;
  deployment_status: string;
  notes: string | null;
}

export interface AssessmentProjectExport {
  customer: string;
  name: string;
  description: string | null;
  status: string;
  start_date: string | null;
  target_completion_date: string | null;
  assignments: ProductAssignmentExport[];
}

export interface AssessmentImportResult {
  project_id: number;
  project_status: "created" | "updated" | "unchanged";
  assignments_created: number;
  assignments_updated: number;
  assignments_unchanged: number;
}

// --------------------------------------------------- Coverage Analysis --

export interface CapabilityCoverageItem {
  id: number;
  code: string;
  name: string;
  domain_id: number;
  domain_name: string;
  covered: boolean;
  provider_count: number;
  providers: string[];
}

export interface DuplicateCapabilityItem {
  id: number;
  code: string;
  name: string;
  domain_id: number;
  domain_name: string;
  provider_count: number;
  providers: string[];
}

export interface DomainCoverage {
  domain_id: number;
  domain_name: string;
  covered_count: number;
  total_count: number;
  coverage_percentage: number;
}

export interface CapabilityMatrix {
  covered: CapabilityCoverageItem[];
  missing: CapabilityCoverageItem[];
  duplicate: DuplicateCapabilityItem[];
}

export interface CoverageReport {
  assessment_project_id: number;
  assessment_project_name: string;
  generated_at: string;
  total_capabilities: number;
  covered_capability_count: number;
  missing_capability_count: number;
  duplicate_capability_count: number;
  overall_coverage_percentage: number;
  domain_coverage: DomainCoverage[];
  covered_capabilities: CapabilityCoverageItem[];
  missing_capabilities: CapabilityCoverageItem[];
  duplicate_capabilities: DuplicateCapabilityItem[];
}

export type CoverageExportFormat = "json" | "excel" | "pdf";
