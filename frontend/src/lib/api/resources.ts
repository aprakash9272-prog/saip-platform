import { apiClient, type BlobDownload } from "@/lib/api/client";
import type {
  AssessmentDashboard,
  AssessmentImportResult,
  AssessmentProject,
  AssessmentProjectExport,
  AssessmentProjectInput,
  BulkOperationResult,
  BusinessUnit,
  BusinessUnitInput,
  Capability,
  CapabilityFacets,
  CapabilityImportSummary,
  CapabilityInput,
  CapabilityMatrix,
  CoverageExportFormat,
  CoverageReport,
  Customer,
  CustomerInput,
  Domain,
  DomainCoverage,
  DomainInput,
  Edition,
  EditionInput,
  Environment,
  EnvironmentInput,
  Framework,
  FrameworkInput,
  FrameworkMapping,
  FrameworkMappingInput,
  Module,
  ModuleInput,
  Paginated,
  Product,
  ProductAssignment,
  ProductAssignmentInput,
  ProductCapabilityMapping,
  ProductCapabilityMappingFacets,
  ProductCapabilityMappingInput,
  ProductInput,
  Vendor,
  VendorInput,
} from "@/lib/api/types";

export interface ListParams {
  skip?: number;
  limit?: number;
  search?: string;
}

// Method-shorthand signatures (rather than arrow-typed properties) so that
// ResourceApi<Concrete, ConcreteInput, ...> stays assignable to the loosely
// typed ResourceApi<EntityRecord, unknown, ...> used by RESOURCE_REGISTRY —
// TypeScript checks method parameters bivariantly, arrow-typed ones strictly.
export interface ResourceApi<TRead, TCreate, TUpdate> {
  list(params?: ListParams): Promise<Paginated<TRead>>;
  get(id: number): Promise<TRead>;
  create(payload: TCreate): Promise<TRead>;
  update(id: number, payload: TUpdate): Promise<TRead>;
  remove(id: number): Promise<void>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

export function createResourceApi<TRead, TCreate, TUpdate = Partial<TCreate>>(
  basePath: string,
): ResourceApi<TRead, TCreate, TUpdate> {
  return {
    list: (params: ListParams = {}) => {
      const qs = buildQuery({
        skip: params.skip,
        limit: params.limit,
        search: params.search,
      });
      return apiClient.get<Paginated<TRead>>(`${basePath}${qs}`);
    },
    get: (id: number) => apiClient.get<TRead>(`${basePath}/${id}`),
    create: (payload: TCreate) => apiClient.post<TRead>(basePath, payload),
    update: (id: number, payload: TUpdate) =>
      apiClient.put<TRead>(`${basePath}/${id}`, payload),
    remove: (id: number) => apiClient.delete(`${basePath}/${id}`),
  };
}

export const vendorsApi = createResourceApi<Vendor, VendorInput>("/vendors");
export const productsApi = createResourceApi<Product, ProductInput>("/products");
export const editionsApi = createResourceApi<Edition, EditionInput>("/editions");
export const modulesApi = createResourceApi<Module, ModuleInput>("/modules");
export const domainsApi = createResourceApi<Domain, DomainInput>("/domains");
export const capabilitiesApi = createResourceApi<Capability, CapabilityInput>(
  "/capabilities",
);
export const frameworksApi = createResourceApi<Framework, FrameworkInput>(
  "/frameworks",
);
export const mappingsApi = createResourceApi<FrameworkMapping, FrameworkMappingInput>(
  "/mappings",
);

export interface CapabilityListParams extends ListParams {
  domain_id?: number;
  risk_category?: string;
}

export function listCapabilities(
  params: CapabilityListParams = {},
): Promise<Paginated<Capability>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    domain_id: params.domain_id,
    risk_category: params.risk_category,
  });
  return apiClient.get<Paginated<Capability>>(`/capabilities${qs}`);
}

export function getCapabilityFacets(): Promise<CapabilityFacets> {
  return apiClient.get<CapabilityFacets>("/capabilities/facets");
}

export function exportCapabilitiesYaml(): Promise<string> {
  return apiClient.getText("/capabilities/export");
}

export function importCapabilitiesYaml(file: File): Promise<CapabilityImportSummary> {
  return apiClient.postFile<CapabilityImportSummary>("/capabilities/import", file);
}

export const productMappingsApi = createResourceApi<
  ProductCapabilityMapping,
  ProductCapabilityMappingInput
>("/product-mappings");

export interface ProductMappingListParams extends ListParams {
  vendor_id?: number;
  product_id?: number;
  edition_id?: number;
  module_id?: number;
  capability_id?: number;
  deployment_model?: string;
  availability_status?: string;
  licensing_tier?: string;
}

export function listProductMappings(
  params: ProductMappingListParams = {},
): Promise<Paginated<ProductCapabilityMapping>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    vendor_id: params.vendor_id,
    product_id: params.product_id,
    edition_id: params.edition_id,
    module_id: params.module_id,
    capability_id: params.capability_id,
    deployment_model: params.deployment_model,
    availability_status: params.availability_status,
    licensing_tier: params.licensing_tier,
  });
  return apiClient.get<Paginated<ProductCapabilityMapping>>(`/product-mappings${qs}`);
}

export function getProductMappingFacets(): Promise<ProductCapabilityMappingFacets> {
  return apiClient.get<ProductCapabilityMappingFacets>("/product-mappings/facets");
}

export function exportProductMappingsYaml(): Promise<string> {
  return apiClient.getText("/product-mappings/export");
}

export function importProductMappingsYaml(
  file: File,
): Promise<CapabilityImportSummary> {
  return apiClient.postFile<CapabilityImportSummary>("/product-mappings/import", file);
}

export function bulkUpdateProductMappings(
  ids: number[],
  patch: Record<string, unknown>,
): Promise<BulkOperationResult> {
  return apiClient.patch<BulkOperationResult>("/product-mappings/bulk", { ids, patch });
}

export function bulkDeleteProductMappings(ids: number[]): Promise<BulkOperationResult> {
  return apiClient.deleteWithBody<BulkOperationResult>("/product-mappings/bulk", { ids });
}

// ------------------------------------------------- Customer Assessment Workspace --

export const customersApi = createResourceApi<Customer, CustomerInput>("/customers");

export interface BusinessUnitListParams extends ListParams {
  customer_id?: number;
}

export const businessUnitsApi = createResourceApi<BusinessUnit, BusinessUnitInput>(
  "/business-units",
);

export function listBusinessUnits(
  params: BusinessUnitListParams = {},
): Promise<Paginated<BusinessUnit>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    customer_id: params.customer_id,
  });
  return apiClient.get<Paginated<BusinessUnit>>(`/business-units${qs}`);
}

export interface EnvironmentListParams extends ListParams {
  customer_id?: number;
  environment_type?: string;
}

export const environmentsApi = createResourceApi<Environment, EnvironmentInput>(
  "/environments",
);

export function listEnvironments(
  params: EnvironmentListParams = {},
): Promise<Paginated<Environment>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    customer_id: params.customer_id,
    environment_type: params.environment_type,
  });
  return apiClient.get<Paginated<Environment>>(`/environments${qs}`);
}

export interface AssessmentProjectListParams extends ListParams {
  customer_id?: number;
  status?: string;
}

export const assessmentProjectsApi = createResourceApi<
  AssessmentProject,
  AssessmentProjectInput
>("/assessment-projects");

export function listAssessmentProjects(
  params: AssessmentProjectListParams = {},
): Promise<Paginated<AssessmentProject>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    customer_id: params.customer_id,
    status: params.status,
  });
  return apiClient.get<Paginated<AssessmentProject>>(`/assessment-projects${qs}`);
}

export function getAssessmentDashboard(projectId: number): Promise<AssessmentDashboard> {
  return apiClient.get<AssessmentDashboard>(`/assessment-projects/${projectId}/dashboard`);
}

export function exportAssessmentProject(
  projectId: number,
): Promise<AssessmentProjectExport> {
  return apiClient.get<AssessmentProjectExport>(`/assessment-projects/${projectId}/export`);
}

export function importAssessmentProject(
  payload: AssessmentProjectExport,
): Promise<AssessmentImportResult> {
  return apiClient.post<AssessmentImportResult>("/assessment-projects/import", payload);
}

export interface ProductAssignmentListParams extends ListParams {
  assessment_project_id?: number;
  vendor_id?: number;
  product_id?: number;
  edition_id?: number;
  environment_id?: number;
  deployment_model?: string;
  deployment_status?: string;
}

export const productAssignmentsApi = createResourceApi<
  ProductAssignment,
  ProductAssignmentInput
>("/product-assignments");

export function listProductAssignments(
  params: ProductAssignmentListParams = {},
): Promise<Paginated<ProductAssignment>> {
  const qs = buildQuery({
    skip: params.skip,
    limit: params.limit,
    search: params.search,
    assessment_project_id: params.assessment_project_id,
    vendor_id: params.vendor_id,
    product_id: params.product_id,
    edition_id: params.edition_id,
    environment_id: params.environment_id,
    deployment_model: params.deployment_model,
    deployment_status: params.deployment_status,
  });
  return apiClient.get<Paginated<ProductAssignment>>(`/product-assignments${qs}`);
}

// --------------------------------------------------- Coverage Analysis --

export function getCoverageReport(assessmentProjectId: number): Promise<CoverageReport> {
  return apiClient.get<CoverageReport>(`/analysis/coverage/${assessmentProjectId}`);
}

export function getDomainSummary(assessmentProjectId: number): Promise<DomainCoverage[]> {
  return apiClient.get<DomainCoverage[]>(
    `/analysis/domain-summary${buildQuery({ assessment_id: assessmentProjectId })}`,
  );
}

export function getCapabilityMatrix(assessmentProjectId: number): Promise<CapabilityMatrix> {
  return apiClient.get<CapabilityMatrix>(
    `/analysis/capabilities${buildQuery({ assessment_id: assessmentProjectId })}`,
  );
}

export function downloadCoverageExport(
  assessmentProjectId: number,
  format: CoverageExportFormat,
): Promise<BlobDownload> {
  const qs = buildQuery({ format });
  return apiClient.getBlob(
    `/analysis/coverage/${assessmentProjectId}/export${qs}`,
    `coverage-${assessmentProjectId}.${format === "excel" ? "xlsx" : format}`,
  );
}
