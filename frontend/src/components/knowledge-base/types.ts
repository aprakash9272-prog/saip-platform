import type { ZodTypeAny } from "zod";

import type { ListParams, ResourceApi } from "@/lib/api/resources";

export type ResourceKey =
  | "vendors"
  | "products"
  | "editions"
  | "modules"
  | "domains"
  | "capabilities"
  | "frameworks"
  | "mappings"
  | "product-mappings"
  | "customers";

export interface ReferenceConfig {
  resourceKey: ResourceKey;
  labelField: string;
}

export interface FieldConfig {
  name: string;
  label: string;
  type:
    | "text"
    | "textarea"
    | "number"
    | "boolean"
    | "reference"
    | "multi-reference"
    | "select"
    | "multi-select";
  required?: boolean;
  placeholder?: string;
  reference?: ReferenceConfig;
  /** Fixed choice list for "select" / "multi-select" fields. */
  options?: readonly string[];
}

export interface ColumnConfig<TRead> {
  key: string;
  header: string;
  // Method shorthand (not an arrow-typed property) so configs for concrete
  // entities stay assignable into the type-erased RESOURCE_REGISTRY.
  render?(item: TRead, referenceMaps: ReferenceMaps): React.ReactNode;
}

export type ReferenceMaps = Record<string, Map<number, string>>;

export interface EntityRecord {
  id: number;
}

/** Read a dynamically-named field off a config-driven entity record. */
export function getFieldValue(item: EntityRecord, key: string): unknown {
  return (item as unknown as Record<string, unknown>)[key];
}

export interface ResourceConfig<
  TRead extends EntityRecord = EntityRecord,
  TCreate = unknown,
  TUpdate = unknown,
> {
  key: ResourceKey;
  title: string;
  description: string;
  labelField: string;
  api: ResourceApi<TRead, TCreate, TUpdate>;
  columns: ColumnConfig<TRead>[];
  fields: FieldConfig[];
  searchPlaceholder: string;
  toFormValues(item: TRead): Record<string, unknown>;
  createSchema: ZodTypeAny;
  updateSchema: ZodTypeAny;
}

export type { ListParams };
