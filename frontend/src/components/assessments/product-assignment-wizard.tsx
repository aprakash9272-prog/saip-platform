"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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
import { ApiError } from "@/lib/api/client";
import {
  editionsApi,
  listEnvironments,
  modulesApi,
  productAssignmentsApi,
  productsApi,
  vendorsApi,
} from "@/lib/api/resources";
import { DEPLOYMENT_MODELS, DEPLOYMENT_STATUSES } from "@/lib/api/types";

interface ProductAssignmentWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assessmentProjectId: number;
  customerId: number;
}

const STEP_LABELS = ["Product", "Assignment details"] as const;

export function ProductAssignmentWizard({
  open,
  onOpenChange,
  assessmentProjectId,
  customerId,
}: ProductAssignmentWizardProps) {
  const queryClient = useQueryClient();

  const [step, setStep] = useState<0 | 1>(0);
  const [vendorId, setVendorId] = useState("");
  const [productId, setProductId] = useState("");
  const [editionId, setEditionId] = useState("");
  const [moduleIds, setModuleIds] = useState<Set<number>>(new Set());
  const [environmentId, setEnvironmentId] = useState("");
  const [licenseQuantity, setLicenseQuantity] = useState("");
  const [deploymentModel, setDeploymentModel] = useState<string>(DEPLOYMENT_MODELS[0]);
  const [deploymentStatus, setDeploymentStatus] = useState<string>(DEPLOYMENT_STATUSES[0]);
  const [notes, setNotes] = useState("");
  const [stepError, setStepError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const vendorsQuery = useResourceOptions("vendors", vendorsApi);
  const productsQuery = useResourceOptions("products", productsApi);
  const editionsQuery = useResourceOptions("editions", editionsApi);
  const modulesQuery = useResourceOptions("modules", modulesApi);
  const environmentsQuery = useQuery({
    queryKey: ["environments", "list", { customer_id: customerId }],
    queryFn: () => listEnvironments({ customer_id: customerId, limit: 200 }),
    enabled: open,
  });

  const products = useMemo(
    () => (productsQuery.data?.items ?? []).filter((p) => String(p.vendor_id) === vendorId),
    [productsQuery.data, vendorId],
  );
  const editions = useMemo(
    () => (editionsQuery.data?.items ?? []).filter((e) => String(e.product_id) === productId),
    [editionsQuery.data, productId],
  );
  const modules = useMemo(
    () => (modulesQuery.data?.items ?? []).filter((m) => String(m.edition_id) === editionId),
    [modulesQuery.data, editionId],
  );
  const environments = environmentsQuery.data?.items ?? [];

  const reset = () => {
    setStep(0);
    setVendorId("");
    setProductId("");
    setEditionId("");
    setModuleIds(new Set());
    setEnvironmentId("");
    setLicenseQuantity("");
    setDeploymentModel(DEPLOYMENT_MODELS[0]);
    setDeploymentStatus(DEPLOYMENT_STATUSES[0]);
    setNotes("");
    setStepError(null);
    setSubmitError(null);
  };

  const handleClose = (nextOpen: boolean) => {
    if (!nextOpen) reset();
    onOpenChange(nextOpen);
  };

  const createMutation = useMutation({
    mutationFn: () =>
      productAssignmentsApi.create({
        assessment_project_id: assessmentProjectId,
        vendor_id: Number(vendorId),
        product_id: Number(productId),
        edition_id: Number(editionId),
        environment_id: Number(environmentId),
        module_ids: Array.from(moduleIds),
        license_quantity: licenseQuantity ? Number(licenseQuantity) : undefined,
        deployment_model: deploymentModel,
        deployment_status: deploymentStatus,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["product-assignments", "list"] });
      queryClient.invalidateQueries({
        queryKey: ["assessment-projects", "dashboard", assessmentProjectId],
      });
      handleClose(false);
    },
  });

  const goNext = () => {
    setStepError(null);
    if (!vendorId || !productId || !editionId) {
      setStepError("Select a vendor, product, and edition to continue.");
      return;
    }
    setStep(1);
  };

  const toggleModule = (id: number) => {
    setModuleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    if (!environmentId) {
      setSubmitError("Select an environment.");
      return;
    }
    try {
      await createMutation.mutateAsync();
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : "Something went wrong.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Assign a Product</DialogTitle>
          <DialogDescription>
            Step {step + 1} of {STEP_LABELS.length}: {STEP_LABELS[step]}
          </DialogDescription>
        </DialogHeader>

        {step === 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Vendor</Label>
              <Select
                value={vendorId}
                onValueChange={(v) => {
                  setVendorId(v);
                  setProductId("");
                  setEditionId("");
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select vendor" />
                </SelectTrigger>
                <SelectContent>
                  {(vendorsQuery.data?.items ?? []).map((v) => (
                    <SelectItem key={v.id} value={String(v.id)}>
                      {v.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Product</Label>
              <Select
                value={productId}
                onValueChange={(v) => {
                  setProductId(v);
                  setEditionId("");
                }}
                disabled={!vendorId}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={vendorId ? "Select product" : "Select a vendor first"} />
                </SelectTrigger>
                <SelectContent>
                  {products.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Edition</Label>
              <Select value={editionId} onValueChange={setEditionId} disabled={!productId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={productId ? "Select edition" : "Select a product first"} />
                </SelectTrigger>
                <SelectContent>
                  {editions.map((e) => (
                    <SelectItem key={e.id} value={String(e.id)}>
                      {e.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {stepError && <p className="text-sm text-destructive">{stepError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => handleClose(false)}>
                Cancel
              </Button>
              <Button type="button" onClick={goNext}>
                Next
              </Button>
            </DialogFooter>
          </div>
        )}

        {step === 1 && (
          <div className="flex flex-col gap-4">
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
              <Label>
                Environment<span className="text-destructive"> *</span>
              </Label>
              <Select value={environmentId} onValueChange={setEnvironmentId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select environment" />
                </SelectTrigger>
                <SelectContent>
                  {environments.map((env) => (
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
            {submitError && <p className="text-sm text-destructive">{submitError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setStep(0)}>
                Back
              </Button>
              <Button type="button" onClick={handleSubmit} disabled={createMutation.isPending}>
                {createMutation.isPending ? "Assigning..." : "Assign Product"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
