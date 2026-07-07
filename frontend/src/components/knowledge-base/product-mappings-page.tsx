"use client";

import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useReferenceMaps } from "@/hooks/use-reference-maps";
import { ApiError } from "@/lib/api/client";
import {
  bulkDeleteProductMappings,
  bulkUpdateProductMappings,
  exportProductMappingsYaml,
  getProductMappingFacets,
  importProductMappingsYaml,
  listProductMappings,
} from "@/lib/api/resources";
import { AVAILABILITY_STATUSES } from "@/lib/api/types";

import { DataTable } from "./data-table";
import { DeleteConfirmDialog } from "./delete-confirm-dialog";
import { EntityDetailSheet } from "./entity-detail-sheet";
import { EntityFormDialog } from "./entity-form-dialog";
import { RESOURCE_REGISTRY } from "./resource-configs";
import type { EntityRecord } from "./types";

const PAGE_SIZE = 10;
const ALL = "__all__";

function downloadYaml(content: string, filename: string): void {
  const blob = new Blob([content], { type: "application/x-yaml" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function ProductMappingsPage() {
  const config = RESOURCE_REGISTRY["product-mappings"];
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [vendorId, setVendorId] = useState<string>(ALL);
  const [deploymentModel, setDeploymentModel] = useState<string>(ALL);
  const [availabilityStatus, setAvailabilityStatus] = useState<string>(ALL);
  const [licensingTier, setLicensingTier] = useState<string>(ALL);

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [activeItem, setActiveItem] = useState<EntityRecord | null>(null);
  const [detailItem, setDetailItem] = useState<EntityRecord | null>(null);
  const [deleteItem, setDeleteItem] = useState<EntityRecord | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkStatus, setBulkStatus] = useState<string>(AVAILABILITY_STATUSES[0]);

  const params = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    search: search || undefined,
    vendor_id: vendorId !== ALL ? Number(vendorId) : undefined,
    deployment_model: deploymentModel !== ALL ? deploymentModel : undefined,
    availability_status: availabilityStatus !== ALL ? availabilityStatus : undefined,
    licensing_tier: licensingTier !== ALL ? licensingTier : undefined,
  };

  const listQuery = useQuery({
    queryKey: ["product-mappings", "list", params],
    queryFn: () => listProductMappings(params),
  });

  const facetsQuery = useQuery({
    queryKey: ["product-mappings", "facets"],
    queryFn: getProductMappingFacets,
  });

  const referenceKeys = useMemo(
    () =>
      Array.from(
        new Set(
          config.fields.filter((f) => f.reference).map((f) => f.reference!.resourceKey),
        ),
      ),
    [config.fields],
  );
  const referenceMaps = useReferenceMaps(referenceKeys);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["product-mappings", "list"] });
    queryClient.invalidateQueries({ queryKey: ["product-mappings", "facets"] });
  };

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => config.api.create(payload),
    onSuccess: invalidate,
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      config.api.update(id, payload),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({
    mutationFn: (id: number) => config.api.remove(id),
    onSuccess: invalidate,
  });
  const importMutation = useMutation({
    mutationFn: (file: File) => importProductMappingsYaml(file),
    onSuccess: (summary) => {
      setImportMessage(
        `Imported: ${summary.created} created, ${summary.updated} updated, ${summary.unchanged} unchanged.`,
      );
      invalidate();
    },
    onError: (error) => {
      setImportMessage(
        error instanceof ApiError ? `Import failed: ${error.message}` : "Import failed.",
      );
    },
  });
  const bulkUpdateMutation = useMutation({
    mutationFn: () =>
      bulkUpdateProductMappings(Array.from(selectedIds), {
        availability_status: bulkStatus,
      }),
    onSuccess: (result) => {
      setBulkMessage(
        `Updated ${result.updated} mapping(s).` +
          (result.failed.length ? ` ${result.failed.length} failed.` : ""),
      );
      setSelectedIds(new Set());
      invalidate();
    },
  });
  const bulkDeleteMutation = useMutation({
    mutationFn: () => bulkDeleteProductMappings(Array.from(selectedIds)),
    onSuccess: (result) => {
      setBulkMessage(
        `Deleted ${result.deleted} mapping(s).` +
          (result.failed.length ? ` ${result.failed.length} failed.` : ""),
      );
      setSelectedIds(new Set());
      invalidate();
    },
  });

  const items = listQuery.data?.items ?? [];
  const total = listQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const openCreate = () => {
    setFormMode("create");
    setActiveItem(null);
    setFormError(null);
    setFormOpen(true);
  };

  const openEdit = (item: EntityRecord) => {
    setFormMode("edit");
    setActiveItem(item);
    setFormError(null);
    setFormOpen(true);
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    setFormError(null);
    try {
      if (formMode === "create") {
        await createMutation.mutateAsync(values);
      } else if (activeItem) {
        await updateMutation.mutateAsync({ id: activeItem.id, payload: values });
      }
      setFormOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Something went wrong.");
    }
  };

  const handleDelete = async () => {
    if (!deleteItem) return;
    await deleteMutation.mutateAsync(deleteItem.id);
    setDeleteItem(null);
  };

  const handleExport = async () => {
    const yamlText = await exportProductMappingsYaml();
    downloadYaml(yamlText, "product-mappings-export.yaml");
  };

  const handleImportFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImportMessage(null);
      importMutation.mutate(file);
    }
    event.target.value = "";
  };

  const toggleSelected = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(items.map((item) => item.id)) : new Set());
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Product Mappings</h2>
        <p className="text-sm text-muted-foreground">{config.description}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder={config.searchPlaceholder}
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(0);
          }}
          className="max-w-xs"
        />
        <Select
          value={vendorId}
          onValueChange={(value) => {
            setVendorId(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All vendors" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All vendors</SelectItem>
            {Array.from(referenceMaps.vendors?.entries() ?? []).map(([id, name]) => (
              <SelectItem key={id} value={String(id)}>
                {name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={deploymentModel}
          onValueChange={(value) => {
            setDeploymentModel(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All deployments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All deployments</SelectItem>
            {(facetsQuery.data?.deployment_models ?? []).map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={availabilityStatus}
          onValueChange={(value) => {
            setAvailabilityStatus(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All statuses</SelectItem>
            {(facetsQuery.data?.availability_statuses ?? []).map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={licensingTier}
          onValueChange={(value) => {
            setLicensingTier(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All tiers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All tiers</SelectItem>
            {(facetsQuery.data?.licensing_tiers ?? []).map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="ml-auto flex flex-wrap gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            className="hidden"
            onChange={handleImportFileChange}
          />
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={importMutation.isPending}
          >
            {importMutation.isPending ? "Importing..." : "Import YAML"}
          </Button>
          <Button variant="outline" onClick={handleExport}>
            Export YAML
          </Button>
          <Button onClick={openCreate}>New Mapping</Button>
        </div>
      </div>

      {importMessage && <p className="text-sm text-muted-foreground">{importMessage}</p>}

      {selectedIds.size > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/40 p-3">
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <Select value={bulkStatus} onValueChange={setBulkStatus}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AVAILABILITY_STATUSES.map((status) => (
                <SelectItem key={status} value={status}>
                  {status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => bulkUpdateMutation.mutate()}
            disabled={bulkUpdateMutation.isPending}
          >
            Set status for selected
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive"
            onClick={() => bulkDeleteMutation.mutate()}
            disabled={bulkDeleteMutation.isPending}
          >
            Delete selected
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setSelectedIds(new Set())}>
            Clear selection
          </Button>
        </div>
      )}
      {bulkMessage && <p className="text-sm text-muted-foreground">{bulkMessage}</p>}

      {listQuery.isError && (
        <p className="text-sm text-destructive">Failed to load product mappings.</p>
      )}

      <DataTable
        columns={config.columns}
        rows={items}
        referenceMaps={referenceMaps}
        loading={listQuery.isLoading}
        getRowId={(item) => item.id}
        onView={setDetailItem}
        onEdit={openEdit}
        onDelete={setDeleteItem}
        selection={{
          selectedIds,
          onToggle: toggleSelected,
          onToggleAll: toggleSelectAll,
        }}
      />

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {total === 0
            ? "No records"
            : `Showing ${params.skip + 1}-${Math.min(params.skip + PAGE_SIZE, total)} of ${total}`}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            Previous
          </Button>
          <span className="self-center text-xs">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>

      <EntityFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        config={config}
        mode={formMode}
        defaultValues={activeItem ? config.toFormValues(activeItem) : undefined}
        onSubmit={handleSubmit}
        submitting={createMutation.isPending || updateMutation.isPending}
        serverError={formError}
      />

      <EntityDetailSheet
        open={!!detailItem}
        onOpenChange={(open) => !open && setDetailItem(null)}
        config={config}
        item={detailItem}
        referenceMaps={referenceMaps}
      />

      <DeleteConfirmDialog
        open={!!deleteItem}
        onOpenChange={(open) => !open && setDeleteItem(null)}
        title="Delete Product Mapping?"
        description="This action cannot be undone."
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
