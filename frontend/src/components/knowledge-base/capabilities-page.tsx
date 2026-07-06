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
import { ApiError } from "@/lib/api/client";
import {
  exportCapabilitiesYaml,
  getCapabilityFacets,
  importCapabilitiesYaml,
  listCapabilities,
} from "@/lib/api/resources";

import { DataTable } from "./data-table";
import { DeleteConfirmDialog } from "./delete-confirm-dialog";
import { EntityDetailSheet } from "./entity-detail-sheet";
import { EntityFormDialog } from "./entity-form-dialog";
import { RESOURCE_REGISTRY } from "./resource-configs";
import type { EntityRecord, ReferenceMaps } from "./types";

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

export function CapabilitiesPage() {
  const config = RESOURCE_REGISTRY.capabilities;
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [domainId, setDomainId] = useState<string>(ALL);
  const [riskCategory, setRiskCategory] = useState<string>(ALL);

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [activeItem, setActiveItem] = useState<EntityRecord | null>(null);
  const [detailItem, setDetailItem] = useState<EntityRecord | null>(null);
  const [deleteItem, setDeleteItem] = useState<EntityRecord | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);

  const params = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    search: search || undefined,
    domain_id: domainId !== ALL ? Number(domainId) : undefined,
    risk_category: riskCategory !== ALL ? riskCategory : undefined,
  };

  const listQuery = useQuery({
    queryKey: ["capabilities", "list", params],
    queryFn: () => listCapabilities(params),
  });

  const facetsQuery = useQuery({
    queryKey: ["capabilities", "facets"],
    queryFn: getCapabilityFacets,
  });

  const referenceMaps: ReferenceMaps = useMemo(() => {
    const domains = new Map<number, string>();
    (facetsQuery.data?.domains ?? []).forEach((d) => domains.set(d.id, d.name));
    return { domains };
  }, [facetsQuery.data]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["capabilities", "list"] });
    queryClient.invalidateQueries({ queryKey: ["capabilities", "facets"] });
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
    mutationFn: (file: File) => importCapabilitiesYaml(file),
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
    const yamlText = await exportCapabilitiesYaml();
    downloadYaml(yamlText, "capabilities-export.yaml");
  };

  const handleImportFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImportMessage(null);
      importMutation.mutate(file);
    }
    event.target.value = "";
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Capabilities</h2>
        <p className="text-sm text-muted-foreground">
          The vendor-neutral security capability taxonomy
          {facetsQuery.data ? ` — ${facetsQuery.data.domains.length} domains covered.` : "."}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search capabilities by name, code, or description..."
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(0);
          }}
          className="max-w-xs"
        />
        <Select
          value={domainId}
          onValueChange={(value) => {
            setDomainId(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-56">
            <SelectValue placeholder="All domains" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All domains</SelectItem>
            {(facetsQuery.data?.domains ?? []).map((domain) => (
              <SelectItem key={domain.id} value={String(domain.id)}>
                {domain.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={riskCategory}
          onValueChange={(value) => {
            setRiskCategory(value);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All risk levels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All risk levels</SelectItem>
            {(facetsQuery.data?.risk_categories ?? []).map((risk) => (
              <SelectItem key={risk} value={risk}>
                {risk}
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
          <Button onClick={openCreate}>New Capability</Button>
        </div>
      </div>

      {importMessage && <p className="text-sm text-muted-foreground">{importMessage}</p>}

      {listQuery.isError && (
        <p className="text-sm text-destructive">Failed to load capabilities.</p>
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
        title="Delete Capability?"
        description="This action cannot be undone."
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
