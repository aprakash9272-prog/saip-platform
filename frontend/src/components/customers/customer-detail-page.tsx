"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AssessmentProjectDialog } from "@/components/customers/assessment-project-dialog";
import { BusinessUnitDialog } from "@/components/customers/business-unit-dialog";
import { EnvironmentDialog } from "@/components/customers/environment-dialog";
import { DeleteConfirmDialog } from "@/components/knowledge-base/delete-confirm-dialog";
import { EntityFormDialog } from "@/components/knowledge-base/entity-form-dialog";
import { RESOURCE_REGISTRY } from "@/components/knowledge-base/resource-configs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError } from "@/lib/api/client";
import {
  businessUnitsApi,
  assessmentProjectsApi,
  customersApi,
  environmentsApi,
  listAssessmentProjects,
  listBusinessUnits,
  listEnvironments,
} from "@/lib/api/resources";
import type { AssessmentProject, BusinessUnit, Environment } from "@/lib/api/types";

const LIST_LIMIT = 200;

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString();
}

function statusVariant(status: string): "default" | "secondary" | "outline" {
  if (status === "Completed") return "default";
  if (status === "Archived") return "outline";
  return "secondary";
}

interface CustomerDetailPageProps {
  customerId: number;
}

export function CustomerDetailPage({ customerId }: CustomerDetailPageProps) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const customerQuery = useQuery({
    queryKey: ["customers", "detail", customerId],
    queryFn: () => customersApi.get(customerId),
  });

  const businessUnitsQuery = useQuery({
    queryKey: ["business-units", "list", { customer_id: customerId }],
    queryFn: () => listBusinessUnits({ customer_id: customerId, limit: LIST_LIMIT }),
  });

  const environmentsQuery = useQuery({
    queryKey: ["environments", "list", { customer_id: customerId }],
    queryFn: () => listEnvironments({ customer_id: customerId, limit: LIST_LIMIT }),
  });

  const projectsQuery = useQuery({
    queryKey: ["assessment-projects", "list", { customer_id: customerId }],
    queryFn: () => listAssessmentProjects({ customer_id: customerId, limit: LIST_LIMIT }),
  });

  // -- Customer edit / delete -----------------------------------------------

  const customerConfig = RESOURCE_REGISTRY.customers;
  const [customerFormOpen, setCustomerFormOpen] = useState(false);
  const [customerFormError, setCustomerFormError] = useState<string | null>(null);
  const [customerDeleteOpen, setCustomerDeleteOpen] = useState(false);

  const updateCustomerMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => customersApi.update(customerId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers", "detail", customerId] });
      queryClient.invalidateQueries({ queryKey: ["customers", "list"] });
    },
  });
  const deleteCustomerMutation = useMutation({
    mutationFn: () => customersApi.remove(customerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers", "list"] });
      router.push("/customers");
    },
  });

  const handleCustomerSubmit = async (values: Record<string, unknown>) => {
    setCustomerFormError(null);
    try {
      await updateCustomerMutation.mutateAsync(values);
      setCustomerFormOpen(false);
    } catch (error) {
      setCustomerFormError(
        error instanceof ApiError ? error.message : "Something went wrong.",
      );
    }
  };

  // -- Business units --------------------------------------------------------

  const [buFormOpen, setBuFormOpen] = useState(false);
  const [buFormMode, setBuFormMode] = useState<"create" | "edit">("create");
  const [activeBu, setActiveBu] = useState<BusinessUnit | null>(null);
  const [buFormError, setBuFormError] = useState<string | null>(null);
  const [buDeleteItem, setBuDeleteItem] = useState<BusinessUnit | null>(null);

  const invalidateBusinessUnits = () =>
    queryClient.invalidateQueries({ queryKey: ["business-units", "list"] });

  const createBuMutation = useMutation({
    mutationFn: (payload: { name: string; description?: string | null }) =>
      businessUnitsApi.create({ ...payload, customer_id: customerId }),
    onSuccess: invalidateBusinessUnits,
  });
  const updateBuMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      businessUnitsApi.update(id, payload),
    onSuccess: invalidateBusinessUnits,
  });
  const deleteBuMutation = useMutation({
    mutationFn: (id: number) => businessUnitsApi.remove(id),
    onSuccess: invalidateBusinessUnits,
  });

  const handleBuSubmit = async (values: { name: string; description?: string | null }) => {
    setBuFormError(null);
    try {
      if (buFormMode === "create") {
        await createBuMutation.mutateAsync(values);
      } else if (activeBu) {
        await updateBuMutation.mutateAsync({ id: activeBu.id, payload: values });
      }
      setBuFormOpen(false);
    } catch (error) {
      setBuFormError(error instanceof ApiError ? error.message : "Something went wrong.");
    }
  };

  // -- Environments -----------------------------------------------------------

  const [envFormOpen, setEnvFormOpen] = useState(false);
  const [envFormMode, setEnvFormMode] = useState<"create" | "edit">("create");
  const [activeEnv, setActiveEnv] = useState<Environment | null>(null);
  const [envFormError, setEnvFormError] = useState<string | null>(null);
  const [envDeleteItem, setEnvDeleteItem] = useState<Environment | null>(null);

  const invalidateEnvironments = () =>
    queryClient.invalidateQueries({ queryKey: ["environments", "list"] });

  const createEnvMutation = useMutation({
    mutationFn: (payload: { name: string; environment_type: string; description?: string | null }) =>
      environmentsApi.create({ ...payload, customer_id: customerId }),
    onSuccess: invalidateEnvironments,
  });
  const updateEnvMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      environmentsApi.update(id, payload),
    onSuccess: invalidateEnvironments,
  });
  const deleteEnvMutation = useMutation({
    mutationFn: (id: number) => environmentsApi.remove(id),
    onSuccess: invalidateEnvironments,
  });

  const handleEnvSubmit = async (values: {
    name: string;
    environment_type: string;
    description?: string | null;
  }) => {
    setEnvFormError(null);
    try {
      if (envFormMode === "create") {
        await createEnvMutation.mutateAsync(values);
      } else if (activeEnv) {
        await updateEnvMutation.mutateAsync({ id: activeEnv.id, payload: values });
      }
      setEnvFormOpen(false);
    } catch (error) {
      setEnvFormError(error instanceof ApiError ? error.message : "Something went wrong.");
    }
  };

  // -- Assessment projects ------------------------------------------------------

  const [projectFormOpen, setProjectFormOpen] = useState(false);
  const [projectFormError, setProjectFormError] = useState<string | null>(null);

  const createProjectMutation = useMutation({
    mutationFn: (payload: {
      name: string;
      status: string;
      start_date?: string | null;
      target_completion_date?: string | null;
      description?: string | null;
    }) => assessmentProjectsApi.create({ ...payload, customer_id: customerId }),
    onSuccess: (project: AssessmentProject) => {
      queryClient.invalidateQueries({ queryKey: ["assessment-projects", "list"] });
      router.push(`/assessments/${project.id}`);
    },
  });

  const handleProjectSubmit = async (values: {
    name: string;
    status: string;
    start_date?: string | null;
    target_completion_date?: string | null;
    description?: string | null;
  }) => {
    setProjectFormError(null);
    try {
      await createProjectMutation.mutateAsync(values);
      setProjectFormOpen(false);
    } catch (error) {
      setProjectFormError(
        error instanceof ApiError ? error.message : "Something went wrong.",
      );
    }
  };

  if (customerQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading customer...</p>;
  }
  if (customerQuery.isError || !customerQuery.data) {
    return <p className="text-sm text-destructive">Failed to load customer.</p>;
  }

  const customer = customerQuery.data;
  const businessUnits = businessUnitsQuery.data?.items ?? [];
  const environments = environmentsQuery.data?.items ?? [];
  const projects = projectsQuery.data?.items ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">{customer.name}</h2>
          <p className="text-sm text-muted-foreground">
            {[customer.industry, customer.headquarters].filter(Boolean).join(" · ") ||
              "No industry or headquarters on file."}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setCustomerFormOpen(true)}>
            <Pencil className="size-4" /> Edit
          </Button>
          <Button variant="outline" onClick={() => setCustomerDeleteOpen(true)}>
            <Trash2 className="size-4 text-destructive" /> Delete
          </Button>
        </div>
      </div>

      {customer.description && (
        <p className="text-sm text-muted-foreground">{customer.description}</p>
      )}

      {/* Business Units */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Business Units</CardTitle>
            <CardDescription>Divisions within {customer.name}.</CardDescription>
          </div>
          <Button
            size="sm"
            onClick={() => {
              setBuFormMode("create");
              setActiveBu(null);
              setBuFormError(null);
              setBuFormOpen(true);
            }}
          >
            <Plus className="size-4" /> Add
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {businessUnits.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center text-muted-foreground">
                      No business units yet.
                    </TableCell>
                  </TableRow>
                )}
                {businessUnits.map((bu) => (
                  <TableRow key={bu.id}>
                    <TableCell>{bu.name}</TableCell>
                    <TableCell>{bu.description ?? "—"}</TableCell>
                    <TableCell className="flex justify-end gap-1 text-right">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                          setBuFormMode("edit");
                          setActiveBu(bu);
                          setBuFormError(null);
                          setBuFormOpen(true);
                        }}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" onClick={() => setBuDeleteItem(bu)}>
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Environments */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Environments</CardTitle>
            <CardDescription>Deployment tiers within {customer.name}&apos;s infrastructure.</CardDescription>
          </div>
          <Button
            size="sm"
            onClick={() => {
              setEnvFormMode("create");
              setActiveEnv(null);
              setEnvFormError(null);
              setEnvFormOpen(true);
            }}
          >
            <Plus className="size-4" /> Add
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {environments.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No environments yet.
                    </TableCell>
                  </TableRow>
                )}
                {environments.map((env) => (
                  <TableRow key={env.id}>
                    <TableCell>{env.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{env.environment_type}</Badge>
                    </TableCell>
                    <TableCell>{env.description ?? "—"}</TableCell>
                    <TableCell className="flex justify-end gap-1 text-right">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                          setEnvFormMode("edit");
                          setActiveEnv(env);
                          setEnvFormError(null);
                          setEnvFormOpen(true);
                        }}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" onClick={() => setEnvDeleteItem(env)}>
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Assessment Projects */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Assessment Projects</CardTitle>
            <CardDescription>Security assessment engagements for {customer.name}.</CardDescription>
          </div>
          <Button
            size="sm"
            onClick={() => {
              setProjectFormError(null);
              setProjectFormOpen(true);
            }}
          >
            <Plus className="size-4" /> New Assessment
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>Target Completion</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No assessment projects yet.
                    </TableCell>
                  </TableRow>
                )}
                {projects.map((project) => (
                  <TableRow key={project.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell>
                      <Link href={`/assessments/${project.id}`} className="hover:underline">
                        {project.name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(project.status)}>{project.status}</Badge>
                    </TableCell>
                    <TableCell>{formatDate(project.start_date)}</TableCell>
                    <TableCell>{formatDate(project.target_completion_date)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <EntityFormDialog
        open={customerFormOpen}
        onOpenChange={setCustomerFormOpen}
        config={customerConfig}
        mode="edit"
        defaultValues={customerConfig.toFormValues(customer)}
        onSubmit={handleCustomerSubmit}
        submitting={updateCustomerMutation.isPending}
        serverError={customerFormError}
      />

      <DeleteConfirmDialog
        open={customerDeleteOpen}
        onOpenChange={setCustomerDeleteOpen}
        title={`Delete ${customer.name}?`}
        description="This will also delete all of its business units, environments, and assessment projects. This action cannot be undone."
        onConfirm={() => deleteCustomerMutation.mutate()}
        loading={deleteCustomerMutation.isPending}
      />

      <BusinessUnitDialog
        open={buFormOpen}
        onOpenChange={setBuFormOpen}
        mode={buFormMode}
        item={activeBu}
        onSubmit={handleBuSubmit}
        submitting={createBuMutation.isPending || updateBuMutation.isPending}
        serverError={buFormError}
      />
      <DeleteConfirmDialog
        open={!!buDeleteItem}
        onOpenChange={(open) => !open && setBuDeleteItem(null)}
        title="Delete Business Unit?"
        description="This action cannot be undone."
        onConfirm={async () => {
          if (buDeleteItem) await deleteBuMutation.mutateAsync(buDeleteItem.id);
          setBuDeleteItem(null);
        }}
        loading={deleteBuMutation.isPending}
      />

      <EnvironmentDialog
        open={envFormOpen}
        onOpenChange={setEnvFormOpen}
        mode={envFormMode}
        item={activeEnv}
        onSubmit={handleEnvSubmit}
        submitting={createEnvMutation.isPending || updateEnvMutation.isPending}
        serverError={envFormError}
      />
      <DeleteConfirmDialog
        open={!!envDeleteItem}
        onOpenChange={(open) => !open && setEnvDeleteItem(null)}
        title="Delete Environment?"
        description="This action cannot be undone."
        onConfirm={async () => {
          if (envDeleteItem) await deleteEnvMutation.mutateAsync(envDeleteItem.id);
          setEnvDeleteItem(null);
        }}
        loading={deleteEnvMutation.isPending}
      />

      <AssessmentProjectDialog
        open={projectFormOpen}
        onOpenChange={setProjectFormOpen}
        mode="create"
        onSubmit={handleProjectSubmit}
        submitting={createProjectMutation.isPending}
        serverError={projectFormError}
      />
    </div>
  );
}
