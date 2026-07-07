"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { DataTable } from "@/components/knowledge-base/data-table";
import { DeleteConfirmDialog } from "@/components/knowledge-base/delete-confirm-dialog";
import { EntityFormDialog } from "@/components/knowledge-base/entity-form-dialog";
import { RESOURCE_REGISTRY } from "@/components/knowledge-base/resource-configs";
import type { EntityRecord } from "@/components/knowledge-base/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useResourceQueries } from "@/hooks/use-resource";
import { ApiError } from "@/lib/api/client";

const PAGE_SIZE = 10;

export function CustomersListPage() {
  const config = RESOURCE_REGISTRY.customers;
  const router = useRouter();

  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [activeItem, setActiveItem] = useState<EntityRecord | null>(null);
  const [deleteItem, setDeleteItem] = useState<EntityRecord | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const params = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    search: search || undefined,
  };
  const { listQuery, createMutation, updateMutation, deleteMutation } =
    useResourceQueries(config.key, config.api, params);

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
        const created = await createMutation.mutateAsync(values);
        setFormOpen(false);
        router.push(`/customers/${created.id}`);
      } else if (activeItem) {
        await updateMutation.mutateAsync({ id: activeItem.id, payload: values });
        setFormOpen(false);
      }
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
        <h2 className="text-2xl font-semibold tracking-tight">Customers</h2>
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
        <Button onClick={openCreate}>New Customer</Button>
      </div>

      {listQuery.isError && (
        <p className="text-sm text-destructive">Failed to load customers.</p>
      )}

      <DataTable
        columns={config.columns}
        rows={items}
        referenceMaps={{}}
        loading={listQuery.isLoading}
        getRowId={(item) => item.id}
        onView={(item) => router.push(`/customers/${item.id}`)}
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

      <DeleteConfirmDialog
        open={!!deleteItem}
        onOpenChange={(open) => !open && setDeleteItem(null)}
        title="Delete Customer?"
        description="This will also delete all of its business units, environments, and assessment projects. This action cannot be undone."
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
