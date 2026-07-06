"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useResourceOptions, useResourceQueries } from "@/hooks/use-resource";
import { ApiError } from "@/lib/api/client";

import { DataTable } from "./data-table";
import { DeleteConfirmDialog } from "./delete-confirm-dialog";
import { EntityDetailSheet } from "./entity-detail-sheet";
import { EntityFormDialog } from "./entity-form-dialog";
import { RESOURCE_REGISTRY } from "./resource-configs";
import type { EntityRecord, ReferenceMaps, ResourceKey } from "./types";
import { getFieldValue } from "./types";

const PAGE_SIZE = 10;

function singular(title: string): string {
  return title.endsWith("s") ? title.slice(0, -1) : title;
}

function useReferenceMaps(referenceKeys: ResourceKey[]): ReferenceMaps {
  const queries = referenceKeys.map((key) =>
    // Reference keys are a fixed, small set derived from static config, so the
    // number of hook calls never changes across renders for a given page.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useResourceOptions(key, RESOURCE_REGISTRY[key].api),
  );

  return useMemo(() => {
    const maps: ReferenceMaps = {};
    referenceKeys.forEach((key, index) => {
      const labelField = RESOURCE_REGISTRY[key].labelField;
      const items = queries[index].data?.items ?? [];
      maps[key] = new Map(
        items.map((item) => [item.id, String(getFieldValue(item, labelField))]),
      );
    });
    return maps;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [referenceKeys, ...queries.map((q) => q.data)]);
}

interface ResourcePageProps {
  resourceKey: ResourceKey;
}

export function ResourcePage({ resourceKey }: ResourcePageProps) {
  const config = RESOURCE_REGISTRY[resourceKey];
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [activeItem, setActiveItem] = useState<EntityRecord | null>(null);
  const [detailItem, setDetailItem] = useState<EntityRecord | null>(null);
  const [deleteItem, setDeleteItem] = useState<EntityRecord | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const params = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    search: search || undefined,
  };
  const { listQuery, createMutation, updateMutation, deleteMutation } =
    useResourceQueries(config.key, config.api, params);

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

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">{config.title}</h2>
        <p className="text-sm text-muted-foreground">{config.description}</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <Input
          placeholder={config.searchPlaceholder}
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(0);
          }}
          className="max-w-sm"
        />
        <Button onClick={openCreate}>New {singular(config.title)}</Button>
      </div>

      {listQuery.isError && (
        <p className="text-sm text-destructive">
          Failed to load {config.title.toLowerCase()}.
        </p>
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
        title={`Delete ${singular(config.title)}?`}
        description="This action cannot be undone."
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
