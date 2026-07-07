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
  is_business_critical: boolean;
  created_at: string;
  updated_at: string;
}

export interface CapabilityInput {
  name: string;
  code: string;
  domain_id: number;
  description?: string | null;
  risk_category?: string | null;
  is_business_critical?: boolean;
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

// -------------------------------------------------------- Gap Analysis --

export const SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low", "Informational"] as const;
export type SeverityLevel = (typeof SEVERITY_LEVELS)[number];

export interface FrameworkControlRef {
  framework_name: string;
  framework_version: string;
  control_id: string;
  control_name: string;
}

export interface GapItem {
  id: number;
  code: string;
  name: string;
  domain_id: number;
  domain_name: string;
  risk_category: string | null;
  severity: string;
  business_impact: string;
  framework_controls: FrameworkControlRef[];
  mapped_products: string[];
  status: string;
}

export interface DomainGapScore {
  domain_id: number;
  domain_name: string;
  coverage_percentage: number;
  gap_percentage: number;
  missing_count: number;
  critical_gap_count: number;
  domain_risk_score: number;
}

export interface GapSummary {
  assessment_project_id: number;
  assessment_project_name: string;
  generated_at: string;
  total_capabilities: number;
  total_gaps: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  informational_count: number;
  overall_gap_percentage: number;
  overall_risk_score: number;
}

export interface GapReport extends GapSummary {
  domain_gap_scores: DomainGapScore[];
  gaps: GapItem[];
}

export type GapExportFormat = "json" | "excel" | "pdf";

// ---------------------------------------------------- Recommendations --

export const PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"] as const;
export type PriorityLevel = (typeof PRIORITY_LEVELS)[number];

export interface ProductCandidate {
  vendor: string;
  product: string;
  edition: string;
  module: string;
  licensing_tier: string | null;
  deployment_model: string;
  supported_platforms: string[];
  availability_status: string;
  already_deployed_vendor: boolean;
  confidence_score: number;
  implementation_complexity: string;
  estimated_effort: string;
}

export interface RecommendationItem {
  capability_id: number;
  capability_code: string;
  capability_name: string;
  domain_id: number;
  domain_name: string;
  severity: string;
  business_impact: string;
  framework_controls: FrameworkControlRef[];
  candidates: ProductCandidate[];
  priority: string;
  domain_coverage_improvement_percentage: number;
  estimated_risk_reduction: number;
}

export interface PriorityBreakdown {
  priority: string;
  count: number;
  capability_codes: string[];
}

export interface ProductComparisonEntry {
  vendor: string;
  product: string;
  gaps_addressed: number;
  average_confidence_score: number;
  domains_covered: string[];
}

export interface CoverageForecast {
  current_coverage_percentage: number;
  projected_coverage_percentage: number;
  addressable_gap_count: number;
  unaddressable_gap_count: number;
}

export interface RecommendationSummary {
  assessment_project_id: number;
  assessment_project_name: string;
  generated_at: string;
  total_gaps: number;
  addressable_gaps: number;
  unaddressable_gaps: number;
  critical_priority_count: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  current_risk_score: number;
  projected_risk_score: number;
  estimated_overall_risk_reduction: number;
  coverage_forecast: CoverageForecast;
}

export interface RecommendationReport extends RecommendationSummary {
  priority_matrix: PriorityBreakdown[];
  product_comparison: ProductComparisonEntry[];
  recommendations: RecommendationItem[];
}

export type RecommendationExportFormat = "json" | "excel" | "pdf";

// ------------------------------------------------- Overlap & Optimization --

export interface DuplicateCapabilityOverlap {
  id: number;
  code: string;
  name: string;
  domain_id: number;
  domain_name: string;
  provider_count: number;
  distinct_vendor_count: number;
  providers: string[];
  cross_vendor: boolean;
}

export interface ProductOverlapPair {
  vendor_a: string;
  product_a: string;
  vendor_b: string;
  product_b: string;
  shared_capability_count: number;
  shared_capability_codes: string[];
  overlap_percentage: number;
}

export interface ModuleOverlapPair {
  vendor_a: string;
  product_a: string;
  module_a: string;
  vendor_b: string;
  product_b: string;
  module_b: string;
  shared_capability_count: number;
  shared_capability_codes: string[];
}

export interface FrameworkOverlapItem {
  framework_name: string;
  framework_version: string;
  control_id: string;
  control_name: string;
  provider_count: number;
  providers: string[];
}

export interface RedundantLicenseItem {
  assignment_id: number;
  vendor: string;
  product: string;
  edition: string;
  license_quantity: number | null;
  redundant_capability_count: number;
  total_capability_count: number;
  redundancy_percentage: number;
  fully_redundant: boolean;
}

export interface UnusedCapabilityItem {
  assignment_id: number;
  vendor: string;
  product: string;
  edition: string;
  module: string;
  capability_code: string;
  capability_name: string;
  domain_name: string;
}

export interface VendorOverlapSummary {
  vendor: string;
  deployed_product_count: number;
  total_capabilities_provided: number;
  unique_capabilities_provided: number;
  overlapping_capabilities_provided: number;
  total_license_quantity: number;
  open_gaps_addressable: number;
}

export interface DomainOverlapScore {
  domain_id: number;
  domain_name: string;
  covered_count: number;
  duplicate_count: number;
  overlap_percentage: number;
}

export interface OverlapSummary {
  assessment_project_id: number;
  assessment_project_name: string;
  generated_at: string;
  total_deployed_products: number;
  total_vendors: number;
  duplicate_capability_count: number;
  cross_vendor_duplicate_count: number;
  unused_capability_count: number;
  overlap_percentage: number;
  optimization_score: number;
  vendor_consolidation_score: number;
  license_reduction_opportunity: number;
  cost_optimization_score: number;
  operational_complexity_score: number;
}

export interface OverlapReport extends OverlapSummary {
  domain_overlap_scores: DomainOverlapScore[];
  duplicate_capabilities: DuplicateCapabilityOverlap[];
  product_overlaps: ProductOverlapPair[];
  module_overlaps: ModuleOverlapPair[];
  framework_overlaps: FrameworkOverlapItem[];
  redundant_licenses: RedundantLicenseItem[];
  unused_capabilities: UnusedCapabilityItem[];
  vendor_summary: VendorOverlapSummary[];
}

export type OverlapExportFormat = "json" | "excel" | "pdf";

// ------------------------------------------------- Scenario Simulation --

export const SCENARIO_TYPES = [
  "add_product",
  "remove_product",
  "replace_product",
  "upgrade_edition",
  "downgrade_edition",
  "enable_module",
  "disable_module",
  "change_licensing_tier",
  "change_deployment_model",
  "change_availability_status",
  "consolidate_vendors",
  "remove_duplicate_products",
] as const;
export type ScenarioType = (typeof SCENARIO_TYPES)[number];

export const SCENARIO_TYPE_LABELS: Record<ScenarioType, string> = {
  add_product: "Add Product",
  remove_product: "Remove Product",
  replace_product: "Replace Product",
  upgrade_edition: "Upgrade Edition",
  downgrade_edition: "Downgrade Edition",
  enable_module: "Enable Module",
  disable_module: "Disable Module",
  change_licensing_tier: "Change Licensing Tier",
  change_deployment_model: "Change Deployment Model",
  change_availability_status: "Change Availability Status",
  consolidate_vendors: "Consolidate Vendors",
  remove_duplicate_products: "Remove Duplicate Products",
};

export type ComparisonClassification = "Improvement" | "Regression" | "Neutral";

export interface SimulationRequest {
  assessment_project_id: number;
  scenario_type: ScenarioType;
  name?: string | null;
  vendor_id?: number | null;
  product_id?: number | null;
  edition_id?: number | null;
  environment_id?: number | null;
  module_ids?: number[] | null;
  license_quantity?: number | null;
  deployment_model?: string | null;
  deployment_status?: string | null;
  notes?: string | null;
  assignment_id?: number | null;
  target_edition_id?: number | null;
  target_module_ids?: number[] | null;
  module_id?: number | null;
  assignment_ids?: number[] | null;
}

export interface MetricComparison {
  metric: string;
  current_value: number;
  proposed_value: number;
  delta: number;
  percentage_change: number;
  classification: ComparisonClassification;
}

export interface CapabilityComparisonItem {
  id: number;
  code: string;
  name: string;
  domain_name: string;
  current_covered: boolean;
  proposed_covered: boolean;
  current_provider_count: number;
  proposed_provider_count: number;
  classification: ComparisonClassification;
}

export interface VendorComparisonItem {
  vendor: string;
  current_deployed: boolean;
  proposed_deployed: boolean;
  current_capability_count: number;
  proposed_capability_count: number;
  current_license_quantity: number;
  proposed_license_quantity: number;
  classification: ComparisonClassification;
}

export interface FrameworkComparisonItem {
  framework_name: string;
  framework_version: string;
  total_controls: number;
  current_satisfied_controls: number;
  proposed_satisfied_controls: number;
  classification: ComparisonClassification;
}

export interface SimulationSummary {
  id: number;
  assessment_project_id: number;
  assessment_project_name: string;
  scenario_type: ScenarioType;
  name: string | null;
  generated_at: string;
  coverage_delta: MetricComparison;
  gap_delta: MetricComparison;
  overlap_delta: MetricComparison;
  recommendation_delta: MetricComparison;
  risk_delta: MetricComparison;
  cost_delta: MetricComparison;
  complexity_delta: MetricComparison;
  vendor_count_delta: MetricComparison;
  license_count_delta: MetricComparison;
  framework_coverage_delta: MetricComparison;
  executive_summary: string[];
}

export interface SimulationReport extends SimulationSummary {
  current_coverage: CoverageReport;
  proposed_coverage: CoverageReport;
  current_gap: GapReport;
  proposed_gap: GapReport;
  current_recommendation: RecommendationReport;
  proposed_recommendation: RecommendationReport;
  current_overlap: OverlapReport;
  proposed_overlap: OverlapReport;
  capability_comparison: CapabilityComparisonItem[];
  vendor_comparison: VendorComparisonItem[];
  framework_comparison: FrameworkComparisonItem[];
}

export type SimulationExportFormat = "json" | "excel" | "pdf";
