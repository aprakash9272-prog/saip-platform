"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useResourceOptions } from "@/hooks/use-resource";
import { listEnvironments, modulesApi } from "@/lib/api/resources";
import {
  DEPLOYMENT_MODELS,
  DEPLOYMENT_STATUSES,
  type ProductAssignment,
} from "@/lib/api/types";

interface ProductAssignmentEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  customerId: number;
  item: ProductAssignment | null;
  vendorName: string;
  productName: string;
  editionName: string;
  onSubmit: (values: {
    environment_id: number;
    module_ids: number[];
    license_quantity?: number | null;
    deployment_model: string;
    deployment_status: string;
    notes?: string | null;
  }) => Promise<void>;
  submitting?: boolean;
  serverError?: string | null;
}

export function ProductAssignmentEditDialog({
  open,
  onOpenChange,
  customerId,
  item,
  vendorName,
  productName,
  editionName,
  onSubmit,
  submitting,
  serverError,
}: ProductAssignmentEditDialogProps) {
  const [environmentId, setEnvironmentId] = useState("");
  const [moduleIds, setModuleIds] = useState<Set<number>>(new Set());
  const [licenseQuantity, setLicenseQuantity] = useState("");
  const [deploymentModel, setDeploymentModel] = useState<string>(DEPLOYMENT_MODELS[0]);
  const [deploymentStatus, setDeploymentStatus] = useState<string>(DEPLOYMENT_STATUSES[0]);
  const [notes, setNotes] = useState("");

  const modulesQuery = useResourceOptions("modules", modulesApi);
  const environmentsQuery = useQuery({
    queryKey: ["environments", "list", { customer_id: customerId }],
    queryFn: () => listEnvironments({ customer_id: customerId, limit: 200 }),
    enabled: open,
  });

  const modules = useMemo(
    () =>
      (modulesQuery.data?.items ?? []).filter(
        (m) => item != null && m.edition_id === item.edition_id,
      ),
    [modulesQuery.data, item],
  );

  useEffect(() => {
    if (open && item) {
      setEnvironmentId(String(item.environment_id));
      setModuleIds(new Set(item.module_ids));
      setLicenseQuantity(item.license_quantity != null ? String(item.license_quantity) : "");
      setDeploymentModel(item.deployment_model);
      setDeploymentStatus(item.deployment_status);
      setNotes(item.notes ?? "");
    }
  }, [open, item]);

  const toggleModule = (id: number) => {
    setModuleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await onSubmit({
      environment_id: Number(environmentId),
      module_ids: Array.from(moduleIds),
      license_quantity: licenseQuantity ? Number(licenseQuantity) : null,
      deployment_model: deploymentModel,
      deployment_status: deploymentStatus,
      notes: notes.trim() || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Edit Product Assignment</DialogTitle>
          <DialogDescription>
            {vendorName} · {productName} · {editionName}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Modules enabled</Label>
            <div className="flex max-h-40 flex-col gap-1 overflow-y-auto rounded-md border p-2">
              {modules.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No modules defined for this edition.
                </p>
              )}
              {modules.map((m) => (
                <label key={m.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={moduleIds.has(m.id)}
                    onChange={() => toggleModule(m.id)}
                    className="size-4 rounded border-input"
                  />
                  {m.name}
                </label>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Environment</Label>
            <Select value={environmentId} onValueChange={setEnvironmentId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select environment" />
              </SelectTrigger>
              <SelectContent>
                {(environmentsQuery.data?.items ?? []).map((env) => (
                  <SelectItem key={env.id} value={String(env.id)}>
                    {env.name} ({env.environment_type})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>License quantity</Label>
              <Input
                type="number"
                min={0}
                value={licenseQuantity}
                onChange={(e) => setLicenseQuantity(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Deployment model</Label>
              <Select value={deploymentModel} onValueChange={setDeploymentModel}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEPLOYMENT_MODELS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Deployment status</Label>
            <Select value={deploymentStatus} onValueChange={setDeploymentStatus}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DEPLOYMENT_STATUSES.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Notes</Label>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          {serverError && <p className="text-sm text-destructive">{serverError}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
