import { z } from "zod";

import {
  capabilitiesApi,
  customersApi,
  domainsApi,
  editionsApi,
  frameworksApi,
  mappingsApi,
  modulesApi,
  productMappingsApi,
  productsApi,
  vendorsApi,
} from "@/lib/api/resources";
import type {
  Capability,
  CapabilityInput,
  Customer,
  CustomerInput,
  Domain,
  DomainInput,
  Edition,
  EditionInput,
  Framework,
  FrameworkInput,
  FrameworkMapping,
  FrameworkMappingInput,
  Module,
  ModuleInput,
  Product,
  ProductCapabilityMapping,
  ProductCapabilityMappingInput,
  ProductInput,
  Vendor,
  VendorInput,
} from "@/lib/api/types";
import {
  AVAILABILITY_STATUSES,
  DEPLOYMENT_MODELS,
  PLATFORMS,
} from "@/lib/api/types";

import type { ResourceConfig, ResourceKey } from "./types";

const optionalText = z
  .string()
  .optional()
  .transform((v) => (v && v.trim().length > 0 ? v.trim() : undefined));

// ---------------------------------------------------------------- Vendors --

export const vendorCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  website: optionalText,
  description: optionalText,
  headquarters: optionalText,
});
export const vendorUpdateSchema = vendorCreateSchema.partial();

const vendorConfig: ResourceConfig<Vendor, VendorInput, Partial<VendorInput>> = {
  key: "vendors",
  title: "Vendors",
  description: "Security vendors tracked in the knowledge base.",
  labelField: "name",
  api: vendorsApi,
  searchPlaceholder: "Search vendors by name, description, or HQ...",
  createSchema: vendorCreateSchema,
  updateSchema: vendorUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    { key: "headquarters", header: "Headquarters" },
    { key: "website", header: "Website" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "website", label: "Website", type: "text", placeholder: "https://..." },
    { name: "headquarters", label: "Headquarters", type: "text" },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    website: item.website ?? "",
    description: item.description ?? "",
    headquarters: item.headquarters ?? "",
  }),
};

// --------------------------------------------------------------- Products --

export const productCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  vendor_id: z.coerce.number({ error: "Vendor is required" }).int().positive(),
  category: optionalText,
  description: optionalText,
  website: optionalText,
});
export const productUpdateSchema = productCreateSchema.partial();

const productConfig: ResourceConfig<Product, ProductInput, Partial<ProductInput>> = {
  key: "products",
  title: "Products",
  description: "Products offered by each vendor.",
  labelField: "name",
  api: productsApi,
  searchPlaceholder: "Search products by name, category, or description...",
  createSchema: productCreateSchema,
  updateSchema: productUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    {
      key: "vendor_id",
      header: "Vendor",
      render: (item, refs) => refs.vendors?.get(item.vendor_id) ?? item.vendor_id,
    },
    { key: "category", header: "Category" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    {
      name: "vendor_id",
      label: "Vendor",
      type: "reference",
      required: true,
      reference: { resourceKey: "vendors", labelField: "name" },
    },
    { name: "category", label: "Category", type: "text" },
    { name: "website", label: "Website", type: "text", placeholder: "https://..." },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    vendor_id: item.vendor_id,
    category: item.category ?? "",
    website: item.website ?? "",
    description: item.description ?? "",
  }),
};

// --------------------------------------------------------------- Editions --

export const editionCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  product_id: z.coerce
    .number({ error: "Product is required" })
    .int()
    .positive(),
  tier: optionalText,
  description: optionalText,
});
export const editionUpdateSchema = editionCreateSchema.partial();

const editionConfig: ResourceConfig<Edition, EditionInput, Partial<EditionInput>> = {
  key: "editions",
  title: "Editions",
  description: "Packaging tiers for each product.",
  labelField: "name",
  api: editionsApi,
  searchPlaceholder: "Search editions by name or tier...",
  createSchema: editionCreateSchema,
  updateSchema: editionUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    {
      key: "product_id",
      header: "Product",
      render: (item, refs) => refs.products?.get(item.product_id) ?? item.product_id,
    },
    { key: "tier", header: "Tier" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    {
      name: "product_id",
      label: "Product",
      type: "reference",
      required: true,
      reference: { resourceKey: "products", labelField: "name" },
    },
    { name: "tier", label: "Tier", type: "text" },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    product_id: item.product_id,
    tier: item.tier ?? "",
    description: item.description ?? "",
  }),
};

// ---------------------------------------------------------------- Modules --

export const moduleCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  edition_id: z.coerce
    .number({ error: "Edition is required" })
    .int()
    .positive(),
  description: optionalText,
  capability_ids: z.array(z.coerce.number()).default([]),
});
export const moduleUpdateSchema = moduleCreateSchema.partial();

const moduleConfig: ResourceConfig<Module, ModuleInput, Partial<ModuleInput>> = {
  key: "modules",
  title: "Modules",
  description: "Capabilities-bearing modules within an edition.",
  labelField: "name",
  api: modulesApi,
  searchPlaceholder: "Search modules by name or description...",
  createSchema: moduleCreateSchema,
  updateSchema: moduleUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    {
      key: "edition_id",
      header: "Edition",
      render: (item, refs) => refs.editions?.get(item.edition_id) ?? item.edition_id,
    },
    {
      key: "capability_ids",
      header: "Capabilities",
      render: (item, refs) =>
        item.capability_ids.length === 0
          ? "—"
          : item.capability_ids
              .map((id) => refs.capabilities?.get(id) ?? id)
              .join(", "),
    },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    {
      name: "edition_id",
      label: "Edition",
      type: "reference",
      required: true,
      reference: { resourceKey: "editions", labelField: "name" },
    },
    {
      name: "capability_ids",
      label: "Capabilities provided",
      type: "multi-reference",
      reference: { resourceKey: "capabilities", labelField: "name" },
    },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    edition_id: item.edition_id,
    description: item.description ?? "",
    capability_ids: item.capability_ids,
  }),
};

// --------------------------------------------------------------- Domains --

export const domainCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: optionalText,
});
export const domainUpdateSchema = domainCreateSchema.partial();

const domainConfig: ResourceConfig<Domain, DomainInput, Partial<DomainInput>> = {
  key: "domains",
  title: "Domains",
  description: "The security domain taxonomy that every capability is classified under.",
  labelField: "name",
  api: domainsApi,
  searchPlaceholder: "Search domains by name or description...",
  createSchema: domainCreateSchema,
  updateSchema: domainUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    { key: "description", header: "Description" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    description: item.description ?? "",
  }),
};

// ----------------------------------------------------------- Capabilities --

export const capabilityCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  code: z
    .string()
    .min(1, "Code is required")
    .regex(
      /^[A-Za-z0-9][A-Za-z0-9._-]*$/,
      "Code must be alphanumeric with optional . _ - separators",
    ),
  domain_id: z.coerce.number({ error: "Domain is required" }).int().positive(),
  description: optionalText,
  risk_category: optionalText,
  is_business_critical: z.boolean().default(false),
});
export const capabilityUpdateSchema = capabilityCreateSchema.partial();

const capabilityConfig: ResourceConfig<Capability, CapabilityInput, Partial<CapabilityInput>> = {
  key: "capabilities",
  title: "Capabilities",
  description: "The vendor-neutral security capability taxonomy.",
  labelField: "name",
  api: capabilitiesApi,
  searchPlaceholder: "Search capabilities by name, code, or description...",
  createSchema: capabilityCreateSchema,
  updateSchema: capabilityUpdateSchema,
  columns: [
    { key: "code", header: "Code" },
    { key: "name", header: "Name" },
    {
      key: "domain_id",
      header: "Domain",
      render: (item, refs) => refs.domains?.get(item.domain_id) ?? item.domain_id,
    },
    { key: "risk_category", header: "Risk Category" },
    {
      key: "is_business_critical",
      header: "Business Critical",
      render: (item) => (item.is_business_critical ? "Yes" : "—"),
    },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "code", label: "Code", type: "text", required: true, placeholder: "EDR-001" },
    {
      name: "domain_id",
      label: "Domain",
      type: "reference",
      required: true,
      reference: { resourceKey: "domains", labelField: "name" },
    },
    { name: "risk_category", label: "Risk Category", type: "text" },
    { name: "is_business_critical", label: "Business Critical", type: "boolean" },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    code: item.code,
    domain_id: item.domain_id,
    risk_category: item.risk_category ?? "",
    is_business_critical: item.is_business_critical,
    description: item.description ?? "",
  }),
};

// ------------------------------------------------------------ Frameworks --

export const frameworkCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  version: z.string().min(1, "Version is required"),
});
export const frameworkUpdateSchema = frameworkCreateSchema.partial();

const frameworkConfig: ResourceConfig<Framework, FrameworkInput, Partial<FrameworkInput>> = {
  key: "frameworks",
  title: "Frameworks",
  description: "Compliance and security frameworks (e.g. NIST CSF, ISO 27001).",
  labelField: "name",
  api: frameworksApi,
  searchPlaceholder: "Search frameworks by name or version...",
  createSchema: frameworkCreateSchema,
  updateSchema: frameworkUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    { key: "version", header: "Version" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "version", label: "Version", type: "text", required: true },
  ],
  toFormValues: (item) => ({
    name: item.name,
    version: item.version,
  }),
};

// -------------------------------------------------------------- Mappings --

export const mappingCreateSchema = z.object({
  capability_id: z.coerce
    .number({ error: "Capability is required" })
    .int()
    .positive(),
  framework_id: z.coerce
    .number({ error: "Framework is required" })
    .int()
    .positive(),
  control_id: z.string().min(1, "Control ID is required"),
  control_name: z.string().min(1, "Control name is required"),
});
export const mappingUpdateSchema = mappingCreateSchema.partial();

const mappingConfig: ResourceConfig<FrameworkMapping, FrameworkMappingInput, Partial<FrameworkMappingInput>> = {
  key: "mappings",
  title: "Framework Mappings",
  description: "Links between capabilities and framework controls.",
  labelField: "control_id",
  api: mappingsApi,
  searchPlaceholder: "Search mappings by control ID or name...",
  createSchema: mappingCreateSchema,
  updateSchema: mappingUpdateSchema,
  columns: [
    {
      key: "capability_id",
      header: "Capability",
      render: (item, refs) =>
        refs.capabilities?.get(item.capability_id) ?? item.capability_id,
    },
    {
      key: "framework_id",
      header: "Framework",
      render: (item, refs) =>
        refs.frameworks?.get(item.framework_id) ?? item.framework_id,
    },
    { key: "control_id", header: "Control ID" },
    { key: "control_name", header: "Control Name" },
  ],
  fields: [
    {
      name: "capability_id",
      label: "Capability",
      type: "reference",
      required: true,
      reference: { resourceKey: "capabilities", labelField: "name" },
    },
    {
      name: "framework_id",
      label: "Framework",
      type: "reference",
      required: true,
      reference: { resourceKey: "frameworks", labelField: "name" },
    },
    { name: "control_id", label: "Control ID", type: "text", required: true },
    { name: "control_name", label: "Control Name", type: "textarea", required: true },
  ],
  toFormValues: (item) => ({
    capability_id: item.capability_id,
    framework_id: item.framework_id,
    control_id: item.control_id,
    control_name: item.control_name,
  }),
};

// ------------------------------------------------------- Product Mappings --

export const productMappingCreateSchema = z.object({
  vendor_id: z.coerce.number({ error: "Vendor is required" }).int().positive(),
  product_id: z.coerce.number({ error: "Product is required" }).int().positive(),
  edition_id: z.coerce.number({ error: "Edition is required" }).int().positive(),
  module_id: z.coerce.number({ error: "Module is required" }).int().positive(),
  capability_id: z.coerce.number({ error: "Capability is required" }).int().positive(),
  licensing_tier: optionalText,
  supported_platforms: z.array(z.string()).default([]),
  deployment_model: z.string().min(1, "Deployment model is required"),
  availability_status: z.string().min(1, "Availability status is required"),
});
export const productMappingUpdateSchema = productMappingCreateSchema.partial();

const productMappingConfig: ResourceConfig<
  ProductCapabilityMapping,
  ProductCapabilityMappingInput,
  Partial<ProductCapabilityMappingInput>
> = {
  key: "product-mappings",
  title: "Product Mappings",
  description:
    "The core mapping layer between vendors, products, editions, modules, and the capabilities they provide.",
  labelField: "id",
  api: productMappingsApi,
  searchPlaceholder: "Search mappings by licensing tier, deployment, or status...",
  createSchema: productMappingCreateSchema,
  updateSchema: productMappingUpdateSchema,
  columns: [
    {
      key: "vendor_id",
      header: "Vendor",
      render: (item, refs) => refs.vendors?.get(item.vendor_id) ?? item.vendor_id,
    },
    {
      key: "product_id",
      header: "Product",
      render: (item, refs) => refs.products?.get(item.product_id) ?? item.product_id,
    },
    {
      key: "module_id",
      header: "Module",
      render: (item, refs) => refs.modules?.get(item.module_id) ?? item.module_id,
    },
    {
      key: "capability_id",
      header: "Capability",
      render: (item, refs) =>
        refs.capabilities?.get(item.capability_id) ?? item.capability_id,
    },
    { key: "licensing_tier", header: "Tier" },
    { key: "deployment_model", header: "Deployment" },
    { key: "availability_status", header: "Status" },
    {
      key: "supported_platforms",
      header: "Platforms",
      render: (item) =>
        item.supported_platforms.length ? item.supported_platforms.join(", ") : "—",
    },
  ],
  fields: [
    {
      name: "vendor_id",
      label: "Vendor",
      type: "reference",
      required: true,
      reference: { resourceKey: "vendors", labelField: "name" },
    },
    {
      name: "product_id",
      label: "Product",
      type: "reference",
      required: true,
      reference: { resourceKey: "products", labelField: "name" },
    },
    {
      name: "edition_id",
      label: "Edition",
      type: "reference",
      required: true,
      reference: { resourceKey: "editions", labelField: "name" },
    },
    {
      name: "module_id",
      label: "Module",
      type: "reference",
      required: true,
      reference: { resourceKey: "modules", labelField: "name" },
    },
    {
      name: "capability_id",
      label: "Capability",
      type: "reference",
      required: true,
      reference: { resourceKey: "capabilities", labelField: "name" },
    },
    { name: "licensing_tier", label: "Licensing Tier", type: "text", placeholder: "Enterprise" },
    {
      name: "supported_platforms",
      label: "Supported Platforms",
      type: "multi-select",
      options: PLATFORMS,
    },
    {
      name: "deployment_model",
      label: "Deployment Model",
      type: "select",
      required: true,
      options: DEPLOYMENT_MODELS,
    },
    {
      name: "availability_status",
      label: "Availability Status",
      type: "select",
      required: true,
      options: AVAILABILITY_STATUSES,
    },
  ],
  toFormValues: (item) => ({
    vendor_id: item.vendor_id,
    product_id: item.product_id,
    edition_id: item.edition_id,
    module_id: item.module_id,
    capability_id: item.capability_id,
    licensing_tier: item.licensing_tier ?? "",
    supported_platforms: item.supported_platforms,
    deployment_model: item.deployment_model,
    availability_status: item.availability_status,
  }),
};

// -------------------------------------------------------------- Customers --

export const customerCreateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  industry: optionalText,
  website: optionalText,
  headquarters: optionalText,
  description: optionalText,
});
export const customerUpdateSchema = customerCreateSchema.partial();

const customerConfig: ResourceConfig<Customer, CustomerInput, Partial<CustomerInput>> = {
  key: "customers",
  title: "Customers",
  description: "Organizations onboarded to the platform for security assessment.",
  labelField: "name",
  api: customersApi,
  searchPlaceholder: "Search customers by name, industry, or headquarters...",
  createSchema: customerCreateSchema,
  updateSchema: customerUpdateSchema,
  columns: [
    { key: "name", header: "Name" },
    { key: "industry", header: "Industry" },
    { key: "headquarters", header: "Headquarters" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "industry", label: "Industry", type: "text" },
    { name: "website", label: "Website", type: "text", placeholder: "https://..." },
    { name: "headquarters", label: "Headquarters", type: "text" },
    { name: "description", label: "Description", type: "textarea" },
  ],
  toFormValues: (item) => ({
    name: item.name,
    industry: item.industry ?? "",
    website: item.website ?? "",
    headquarters: item.headquarters ?? "",
    description: item.description ?? "",
  }),
};

export const RESOURCE_REGISTRY: Record<ResourceKey, ResourceConfig> = {
  vendors: vendorConfig,
  products: productConfig,
  editions: editionConfig,
  modules: moduleConfig,
  domains: domainConfig,
  capabilities: capabilityConfig,
  frameworks: frameworkConfig,
  mappings: mappingConfig,
  "product-mappings": productMappingConfig,
  customers: customerConfig,
};
