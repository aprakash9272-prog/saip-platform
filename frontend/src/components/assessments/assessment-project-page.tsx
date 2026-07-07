"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Blocks,
  Building2,
  Download,
  Layers,
  Package,
  Pencil,
  Plus,
  ShieldAlert,
  ShieldCheck,
  Tags,
  Trash2,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { AssessmentProjectDialog } from "@/components/customers/assessment-project-dialog";
import { DeleteConfirmDialog } from "@/components/knowledge-base/delete-confirm-dialog";
import { useReferenceMaps } from "@/hooks/use-reference-maps";
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
  assessmentProjectsApi,
  customersApi,
  exportAssessmentProject,
  getAssessmentDashboard,
  importAssessmentProject,
  listEnvironments,
  listProductAssignments,
  productAssignmentsApi,
} from "@/lib/api/resources";
import type { ProductAssignment } from "@/lib/api/types";

import { CoverageAnalysisSection } from "./coverage-analysis-section";
import { ProductAssignmentEditDialog } from "./product-assignment-edit-dialog";
import { ProductAssignmentWizard } from "./product-assignment-wizard";

function statusVariant(status: string): "default" | "secondary" | "outline" {
  if (status === "Completed") return "default";
  if (status === "Archived") return "outline";
  return "secondary";
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString();
}

function downloadJson(content: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(content, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

interface AssessmentProjectPageProps {
  projectId: number;
}

export function AssessmentProjectPage({ projectId }: AssessmentProjectPageProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const projectQuery = useQuery({
    queryKey: ["assessment-projects", "detail", projectId],
    queryFn: () => assessmentProjectsApi.get(projectId),
  });

  const customerQuery = useQuery({
    queryKey: ["customers", "detail", projectQuery.data?.customer_id],
    queryFn: () => customersApi.get(projectQuery.data!.customer_id),
    enabled: !!projectQuery.data,
  });

  const dashboardQuery = useQuery({
    queryKey: ["assessment-projects", "dashboard", projectId],
    queryFn: () => getAssessmentDashboard(projectId),
  });

  const assignmentsQuery = useQuery({
    queryKey: ["product-assignments", "list", { assessment_project_id: projectId }],
    queryFn: () => listProductAssignments({ assessment_project_id: projectId, limit: 200 }),
  });

  const referenceMaps = useReferenceMaps(["vendors", "products", "editions", "modules"]);
  const vendorMap = referenceMaps.vendors;
  const productMap = referenceMaps.products;
  const editionMap = referenceMaps.editions;

  const environmentsQuery = useQuery({
    queryKey: ["environments", "list", { customer_id: projectQuery.data?.customer_id }],
    queryFn: () => listEnvironments({ customer_id: projectQuery.data!.customer_id, limit: 200 }),
    enabled: !!projectQuery.data,
  });
  const environmentMap = new Map(
    (environmentsQuery.data?.items ?? []).map((env) => [env.id, env.name]),
  );

  // -- project edit / delete ------------------------------------------------

  const [projectFormOpen, setProjectFormOpen] = useState(false);
  const [projectFormError, setProjectFormError] = useState<string | null>(null);
  const [projectDeleteOpen, setProjectDeleteOpen] = useState(false);

  const updateProjectMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      assessmentProjectsApi.update(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessment-projects", "detail", projectId] });
    },
  });
  const deleteProjectMutation = useMutation({
    mutationFn: () => assessmentProjectsApi.remove(projectId),
    onSuccess: () => {
      if (projectQuery.data) {
        router.push(`/customers/${projectQuery.data.customer_id}`);
      } else {
        router.push("/customers");
      }
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
      await updateProjectMutation.mutateAsync(values);
      setProjectFormOpen(false);
    } catch (error) {
      setProjectFormError(
        error instanceof ApiError ? error.message : "Something went wrong.",
      );
    }
  };

  // -- product assignments ---------------------------------------------------

  const [wizardOpen, setWizardOpen] = useState(false);
  const [editItem, setEditItem] = useState<ProductAssignment | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [deleteItem, setDeleteItem] = useState<ProductAssignment | null>(null);

  const invalidateAssignments = () => {
    queryClient.invalidateQueries({ queryKey: ["product-assignments", "list"] });
    queryClient.invalidateQueries({
      queryKey: ["assessment-projects", "dashboard", projectId],
    });
  };

  const updateAssignmentMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      productAssignmentsApi.update(id, payload),
    onSuccess: invalidateAssignments,
  });
  const deleteAssignmentMutation = useMutation({
    mutationFn: (id: number) => productAssignmentsApi.remove(id),
    onSuccess: invalidateAssignments,
  });

  const handleEditSubmit = async (values: {
    environment_id: number;
    module_ids: number[];
    license_quantity?: number | null;
    deployment_model: string;
    deployment_status: string;
    notes?: string | null;
  }) => {
    if (!editItem) return;
    setEditError(null);
    try {
      await updateAssignmentMutation.mutateAsync({ id: editItem.id, payload: values });
      setEditItem(null);
    } catch (error) {
      setEditError(error instanceof ApiError ? error.message : "Something went wrong.");
    }
  };

  // -- import / export --------------------------------------------------------

  const [importMessage, setImportMessage] = useState<string | null>(null);

  const handleExport = async () => {
    const data = await exportAssessmentProject(projectId);
    downloadJson(data, `${data.name.replace(/\s+/g, "-").toLowerCase()}-export.json`);
  };

  const importMutation = useMutation({
    mutationFn: (payload: unknown) => importAssessmentProject(payload as never),
    onSuccess: (result) => {
      setImportMessage(
        `Project ${result.project_status}. Assignments: ${result.assignments_created} created, ${result.assignments_updated} updated, ${result.assignments_unchanged} unchanged.`,
      );
      queryClient.invalidateQueries({ queryKey: ["assessment-projects"] });
      invalidateAssignments();
    },
    onError: (error) => {
      setImportMessage(
        error instanceof ApiError ? `Import failed: ${error.message}` : "Import failed.",
      );
    },
  });

  const handleImportFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImportMessage(null);
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const payload = JSON.parse(reader.result as string);
          importMutation.mutate(payload);
        } catch {
          setImportMessage("Import failed: invalid JSON file.");
        }
      };
      reader.readAsText(file);
    }
    event.target.value = "";
  };

  if (projectQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading assessment project...</p>;
  }
  if (projectQuery.isError || !projectQuery.data) {
    return <p className="text-sm text-destructive">Failed to load assessment project.</p>;
  }

  const project = projectQuery.data;
  const dashboard = dashboardQuery.data;
  const assignments = assignmentsQuery.data?.items ?? [];

  const dashboardCards = [
    { title: "Deployed Products", value: dashboard?.total_deployed_products, icon: Package },
    { title: "Vendors In Use", value: dashboard?.vendor_count, icon: Building2 },
    { title: "Modules Enabled", value: dashboard?.module_count, icon: Blocks },
    { title: "Capabilities Available", value: dashboard?.capability_count, icon: ShieldCheck },
    { title: "Security Domains", value: dashboard?.domain_count, icon: Tags },
    { title: "Frameworks Represented", value: dashboard?.framework_count, icon: Layers },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          {customerQuery.data && (
            <Link
              href={`/customers/${customerQuery.data.id}`}
              className="text-sm text-muted-foreground hover:underline"
            >
              {customerQuery.data.name}
            </Link>
          )}
          <h2 className="text-2xl font-semibold tracking-tight">{project.name}</h2>
          <div className="mt-1 flex items-center gap-2">
            <Badge variant={statusVariant(project.status)}>{project.status}</Badge>
            <span className="text-xs text-muted-foreground">
              {formatDate(project.start_date)} &rarr; {formatDate(project.target_completion_date)}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href={`/assessments/${projectId}/gaps`}>
              <ShieldAlert className="size-4" /> Gap Analysis
            </Link>
          </Button>
          <Button variant="outline" onClick={() => setProjectFormOpen(true)}>
            <Pencil className="size-4" /> Edit
          </Button>
          <Button variant="outline" onClick={() => setProjectDeleteOpen(true)}>
            <Trash2 className="size-4 text-destructive" /> Delete
          </Button>
        </div>
      </div>

      {project.description && (
        <p className="text-sm text-muted-foreground">{project.description}</p>
      )}

      {/* Dashboard */}
      <div>
        <h3 className="mb-2 text-lg font-semibold tracking-tight">Dashboard</h3>
        <p className="mb-3 text-xs text-muted-foreground">
          Informational rollup of what has been deployed. Coverage, gap, and overlap
          analysis will be introduced in a future sprint.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {dashboardCards.map((card) => (
            <Card key={card.title}>
              <CardHeader>
                <card.icon className="size-5 text-muted-foreground" />
                <CardTitle className="text-2xl">{card.value ?? "—"}</CardTitle>
                <CardDescription>{card.title}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>

      {/* Coverage Analysis */}
      <CoverageAnalysisSection projectId={projectId} />

      {/* Product Assignments */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Product Assignments</CardTitle>
            <CardDescription>
              Products from the knowledge base deployed within this assessment.
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleImportFileChange}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={importMutation.isPending}
            >
              <Upload className="size-4" />
              {importMutation.isPending ? "Importing..." : "Import JSON"}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="size-4" /> Export JSON
            </Button>
            <Button size="sm" onClick={() => setWizardOpen(true)}>
              <Plus className="size-4" /> Add Product
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {importMessage && <p className="text-sm text-muted-foreground">{importMessage}</p>}
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Edition</TableHead>
                  <TableHead>Modules</TableHead>
                  <TableHead>Environment</TableHead>
                  <TableHead>License Qty</TableHead>
                  <TableHead>Deployment</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assignments.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground">
                      No products assigned yet.
                    </TableCell>
                  </TableRow>
                )}
                {assignments.map((assignment) => (
                  <TableRow key={assignment.id}>
                    <TableCell>{vendorMap?.get(assignment.vendor_id) ?? assignment.vendor_id}</TableCell>
                    <TableCell>{productMap?.get(assignment.product_id) ?? assignment.product_id}</TableCell>
                    <TableCell>{editionMap?.get(assignment.edition_id) ?? assignment.edition_id}</TableCell>
                    <TableCell>
                      {assignment.module_ids.length === 0
                        ? "—"
                        : assignment.module_ids
                            .map((id) => referenceMaps.modules?.get(id) ?? id)
                            .join(", ")}
                    </TableCell>
                    <TableCell>
                      {environmentMap.get(assignment.environment_id) ??
                        assignment.environment_id}
                    </TableCell>
                    <TableCell>{assignment.license_quantity ?? "—"}</TableCell>
                    <TableCell>{assignment.deployment_model}</TableCell>
                    <TableCell>{assignment.deployment_status}</TableCell>
                    <TableCell className="flex justify-end gap-1 text-right">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                          setEditError(null);
                          setEditItem(assignment);
                        }}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setDeleteItem(assignment)}
                      >
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

      <AssessmentProjectDialog
        open={projectFormOpen}
        onOpenChange={setProjectFormOpen}
        mode="edit"
        item={project}
        onSubmit={handleProjectSubmit}
        submitting={updateProjectMutation.isPending}
        serverError={projectFormError}
      />

      <DeleteConfirmDialog
        open={projectDeleteOpen}
        onOpenChange={setProjectDeleteOpen}
        title={`Delete ${project.name}?`}
        description="This will also delete all of its product assignments. This action cannot be undone."
        onConfirm={() => deleteProjectMutation.mutate()}
        loading={deleteProjectMutation.isPending}
      />

      {project && (
        <ProductAssignmentWizard
          open={wizardOpen}
          onOpenChange={setWizardOpen}
          assessmentProjectId={projectId}
          customerId={project.customer_id}
        />
      )}

      <ProductAssignmentEditDialog
        open={!!editItem}
        onOpenChange={(open) => !open && setEditItem(null)}
        customerId={project.customer_id}
        item={editItem}
        vendorName={editItem ? vendorMap?.get(editItem.vendor_id) ?? "" : ""}
        productName={editItem ? productMap?.get(editItem.product_id) ?? "" : ""}
        editionName={editItem ? editionMap?.get(editItem.edition_id) ?? "" : ""}
        onSubmit={handleEditSubmit}
        submitting={updateAssignmentMutation.isPending}
        serverError={editError}
      />

      <DeleteConfirmDialog
        open={!!deleteItem}
        onOpenChange={(open) => !open && setDeleteItem(null)}
        title="Delete Product Assignment?"
        description="This action cannot be undone."
        onConfirm={async () => {
          if (deleteItem) await deleteAssignmentMutation.mutateAsync(deleteItem.id);
          setDeleteItem(null);
        }}
        loading={deleteAssignmentMutation.isPending}
      />
    </div>
  );
}
