"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download, FlaskConical } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useResourceOptions } from "@/hooks/use-resource";
import { ApiError } from "@/lib/api/client";
import {
  assessmentProjectsApi,
  downloadSimulationExport,
  editionsApi,
  listEnvironments,
  listProductAssignments,
  modulesApi,
  productsApi,
  runSimulation,
  vendorsApi,
} from "@/lib/api/resources";
import {
  DEPLOYMENT_MODELS,
  DEPLOYMENT_STATUSES,
  SCENARIO_TYPES,
  SCENARIO_TYPE_LABELS,
} from "@/lib/api/types";
import type {
  ComparisonClassification,
  ScenarioType,
  SimulationExportFormat,
  SimulationReport,
  SimulationRequest,
} from "@/lib/api/types";

const NEW_ASSIGNMENT_SCENARIOS: ScenarioType[] = ["add_product", "replace_product"];
const EXISTING_ASSIGNMENT_SCENARIOS: ScenarioType[] = [
  "remove_product",
  "replace_product",
  "upgrade_edition",
  "downgrade_edition",
  "change_licensing_tier",
  "enable_module",
  "disable_module",
  "change_deployment_model",
  "change_availability_status",
];
const EDITION_SWAP_SCENARIOS: ScenarioType[] = [
  "upgrade_edition",
  "downgrade_edition",
  "change_licensing_tier",
];
const MODULE_TOGGLE_SCENARIOS: ScenarioType[] = ["enable_module", "disable_module"];
const BULK_REMOVE_SCENARIOS: ScenarioType[] = [
  "consolidate_vendors",
  "remove_duplicate_products",
];

function classificationBadge(classification: ComparisonClassification) {
  if (classification === "Improvement") {
    return (
      <Badge className="bg-emerald-600 text-white dark:bg-emerald-600 dark:text-white">
        Improvement
      </Badge>
    );
  }
  if (classification === "Regression") {
    return (
      <Badge className="bg-red-600 text-white dark:bg-red-600 dark:text-white">Regression</Badge>
    );
  }
  return <Badge variant="outline">Neutral</Badge>;
}

function heatStyle(pct: number): React.CSSProperties {
  const hue = Math.max(0, Math.min(120, (pct / 100) * 120));
  return { backgroundColor: `hsl(${hue}, 70%, 45%)`, color: "white" };
}

interface SimulationPageProps {
  projectId: number;
}

export function SimulationPage({ projectId }: SimulationPageProps) {
  const projectQuery = useQuery({
    queryKey: ["assessment-projects", "detail", projectId],
    queryFn: () => assessmentProjectsApi.get(projectId),
  });
  const customerId = projectQuery.data?.customer_id;

  const assignmentsQuery = useQuery({
    queryKey: ["product-assignments", "list", { assessment_project_id: projectId }],
    queryFn: () => listProductAssignments({ assessment_project_id: projectId, limit: 200 }),
  });
  const assignments = useMemo(() => assignmentsQuery.data?.items ?? [], [assignmentsQuery.data]);

  const vendorsQuery = useResourceOptions("vendors", vendorsApi);
  const productsQuery = useResourceOptions("products", productsApi);
  const editionsQuery = useResourceOptions("editions", editionsApi);
  const modulesQuery = useResourceOptions("modules", modulesApi);
  const environmentsQuery = useQuery({
    queryKey: ["environments", "list", { customer_id: customerId }],
    queryFn: () => listEnvironments({ customer_id: customerId!, limit: 200 }),
    enabled: !!customerId,
  });

  const vendorMap = new Map((vendorsQuery.data?.items ?? []).map((v) => [v.id, v.name]));
  const productMap = new Map((productsQuery.data?.items ?? []).map((p) => [p.id, p.name]));
  const editionMap = new Map((editionsQuery.data?.items ?? []).map((e) => [e.id, e.name]));
  const moduleMap = new Map((modulesQuery.data?.items ?? []).map((m) => [m.id, m.name]));

  const assignmentLabel = (assignmentId: number) => {
    const assignment = assignments.find((a) => a.id === assignmentId);
    if (!assignment) return `Assignment ${assignmentId}`;
    return `${vendorMap.get(assignment.vendor_id) ?? assignment.vendor_id} — ${
      productMap.get(assignment.product_id) ?? assignment.product_id
    } (${editionMap.get(assignment.edition_id) ?? assignment.edition_id})`;
  };

  // -- scenario builder state -----------------------------------------------

  const [scenarioType, setScenarioType] = useState<ScenarioType>("add_product");
  const [name, setName] = useState("");
  const [vendorId, setVendorId] = useState("");
  const [productId, setProductId] = useState("");
  const [editionId, setEditionId] = useState("");
  const [moduleIds, setModuleIds] = useState<Set<number>>(new Set());
  const [environmentId, setEnvironmentId] = useState("");
  const [licenseQuantity, setLicenseQuantity] = useState("");
  const [deploymentModel, setDeploymentModel] = useState<string>(DEPLOYMENT_MODELS[0]);
  const [assignmentId, setAssignmentId] = useState("");
  const [targetEditionId, setTargetEditionId] = useState("");
  const [targetModuleIds, setTargetModuleIds] = useState<Set<number>>(new Set());
  const [toggleModuleId, setToggleModuleId] = useState("");
  const [deploymentStatus, setDeploymentStatus] = useState<string>(DEPLOYMENT_STATUSES[2]);
  const [bulkAssignmentIds, setBulkAssignmentIds] = useState<Set<number>>(new Set());
  const [formError, setFormError] = useState<string | null>(null);

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

  const selectedAssignment = useMemo(
    () => assignments.find((a) => String(a.id) === assignmentId),
    [assignments, assignmentId],
  );
  const targetEditions = useMemo(
    () =>
      selectedAssignment
        ? (editionsQuery.data?.items ?? []).filter(
            (e) => e.product_id === selectedAssignment.product_id,
          )
        : [],
    [editionsQuery.data, selectedAssignment],
  );
  const targetModules = useMemo(
    () => (modulesQuery.data?.items ?? []).filter((m) => String(m.edition_id) === targetEditionId),
    [modulesQuery.data, targetEditionId],
  );
  const enabledModuleOptions = useMemo(() => {
    if (!selectedAssignment) return [];
    const editionModules = (modulesQuery.data?.items ?? []).filter(
      (m) => m.edition_id === selectedAssignment.edition_id,
    );
    if (scenarioType === "enable_module") {
      return editionModules.filter((m) => !selectedAssignment.module_ids.includes(m.id));
    }
    return editionModules.filter((m) => selectedAssignment.module_ids.includes(m.id));
  }, [modulesQuery.data, selectedAssignment, scenarioType]);

  const toggleModule = (id: number) => {
    setModuleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const toggleTargetModule = (id: number) => {
    setTargetModuleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const toggleBulkAssignment = (id: number) => {
    setBulkAssignmentIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const showNewAssignmentFields = NEW_ASSIGNMENT_SCENARIOS.includes(scenarioType);
  const showExistingAssignment = EXISTING_ASSIGNMENT_SCENARIOS.includes(scenarioType);
  const showEditionSwap = EDITION_SWAP_SCENARIOS.includes(scenarioType);
  const showModuleToggle = MODULE_TOGGLE_SCENARIOS.includes(scenarioType);
  const showDeploymentModelField =
    showNewAssignmentFields || scenarioType === "change_deployment_model";
  const showDeploymentStatusField = scenarioType === "change_availability_status";
  const showBulkAssignments = BULK_REMOVE_SCENARIOS.includes(scenarioType);

  const [report, setReport] = useState<SimulationReport | null>(null);

  const simulateMutation = useMutation({
    mutationFn: (payload: SimulationRequest) => runSimulation(payload),
    onSuccess: (result) => setReport(result),
  });

  const handleRunSimulation = async () => {
    setFormError(null);
    const payload: SimulationRequest = {
      assessment_project_id: projectId,
      scenario_type: scenarioType,
      name: name.trim() || undefined,
    };

    if (showNewAssignmentFields) {
      if (!vendorId || !productId || !editionId || !environmentId) {
        setFormError("Select a vendor, product, edition, and environment.");
        return;
      }
      payload.vendor_id = Number(vendorId);
      payload.product_id = Number(productId);
      payload.edition_id = Number(editionId);
      payload.environment_id = Number(environmentId);
      payload.module_ids = Array.from(moduleIds);
      payload.license_quantity = licenseQuantity ? Number(licenseQuantity) : undefined;
      payload.deployment_model = deploymentModel;
    }
    if (showExistingAssignment) {
      if (!assignmentId) {
        setFormError("Select the product assignment this scenario applies to.");
        return;
      }
      payload.assignment_id = Number(assignmentId);
    }
    if (showEditionSwap) {
      if (!targetEditionId) {
        setFormError("Select the target edition.");
        return;
      }
      payload.target_edition_id = Number(targetEditionId);
      payload.target_module_ids = Array.from(targetModuleIds);
    }
    if (showModuleToggle) {
      if (!toggleModuleId) {
        setFormError("Select the module to toggle.");
        return;
      }
      payload.module_id = Number(toggleModuleId);
    }
    if (showDeploymentModelField) {
      payload.deployment_model = deploymentModel;
    }
    if (showDeploymentStatusField) {
      payload.deployment_status = deploymentStatus;
    }
    if (showBulkAssignments) {
      if (bulkAssignmentIds.size === 0) {
        setFormError("Select at least one product assignment to remove.");
        return;
      }
      payload.assignment_ids = Array.from(bulkAssignmentIds);
    }

    try {
      await simulateMutation.mutateAsync(payload);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Simulation failed.");
    }
  };

  const [exportingFormat, setExportingFormat] = useState<SimulationExportFormat | null>(null);
  const handleExport = async (format: SimulationExportFormat) => {
    if (!report) return;
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadSimulationExport(report.id, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportingFormat(null);
    }
  };

  const deltaFields: { key: keyof SimulationReport; label: string }[] = [
    { key: "coverage_delta", label: "Coverage" },
    { key: "gap_delta", label: "Gap" },
    { key: "overlap_delta", label: "Overlap" },
    { key: "recommendation_delta", label: "Remaining Risk Reduction" },
    { key: "risk_delta", label: "Risk Score" },
    { key: "cost_delta", label: "Cost Optimization" },
    { key: "complexity_delta", label: "Complexity" },
    { key: "vendor_count_delta", label: "Vendor Count" },
    { key: "license_count_delta", label: "License Count" },
    { key: "framework_coverage_delta", label: "Framework Coverage" },
  ];

  const percentChartData = useMemo(() => {
    if (!report) return [];
    return [
      { name: "Coverage %", Current: report.coverage_delta.current_value, Proposed: report.coverage_delta.proposed_value },
      { name: "Gap %", Current: report.gap_delta.current_value, Proposed: report.gap_delta.proposed_value },
      { name: "Overlap %", Current: report.overlap_delta.current_value, Proposed: report.overlap_delta.proposed_value },
      { name: "Risk Score", Current: report.risk_delta.current_value, Proposed: report.risk_delta.proposed_value },
      { name: "Cost Score", Current: report.cost_delta.current_value, Proposed: report.cost_delta.proposed_value },
      { name: "Complexity", Current: report.complexity_delta.current_value, Proposed: report.complexity_delta.proposed_value },
      { name: "Framework %", Current: report.framework_coverage_delta.current_value, Proposed: report.framework_coverage_delta.proposed_value },
    ];
  }, [report]);

  if (projectQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading assessment project...</p>;
  }
  if (projectQuery.isError || !projectQuery.data) {
    return <p className="text-sm text-destructive">Failed to load assessment project.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href={`/assessments/${projectId}`}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:underline"
        >
          <ArrowLeft className="size-3.5" /> {projectQuery.data.name}
        </Link>
        <h2 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <FlaskConical className="size-6" /> Scenario Simulation
        </h2>
        <p className="text-xs text-muted-foreground">
          Simulate a hypothetical architecture change and see its exact before/after impact on
          coverage, gaps, overlap, and recommendations — deterministic calculations only, nothing
          is written to the real assessment.
        </p>
      </div>

      {/* Scenario Builder */}
      <Card>
        <CardHeader>
          <CardTitle>Scenario Builder</CardTitle>
          <CardDescription>
            Choose a scenario type and fill in the fields it needs, then run the simulation.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label>Scenario Type</Label>
              <Select value={scenarioType} onValueChange={(v) => setScenarioType(v as ScenarioType)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SCENARIO_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {SCENARIO_TYPE_LABELS[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Scenario Name (optional)</Label>
              <Input
                placeholder="e.g. Replace CrowdStrike with SentinelOne"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>

          {showNewAssignmentFields && (
            <div className="flex flex-col gap-4 rounded-md border p-3">
              <p className="text-xs font-medium text-muted-foreground">
                {scenarioType === "replace_product" ? "New product to add" : "Product to add"}
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
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
                      <SelectValue placeholder="Select product" />
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
                      <SelectValue placeholder="Select edition" />
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
                <div className="flex flex-col gap-1.5">
                  <Label>Environment</Label>
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
                <div className="flex flex-col gap-1.5">
                  <Label>License Quantity</Label>
                  <Input
                    type="number"
                    min={0}
                    value={licenseQuantity}
                    onChange={(e) => setLicenseQuantity(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Modules to enable</Label>
                <div className="flex max-h-32 flex-col gap-1 overflow-y-auto rounded-md border p-2">
                  {modules.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      {editionId ? "No modules defined for this edition." : "Select an edition first."}
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
            </div>
          )}

          {showExistingAssignment && (
            <div className="flex flex-col gap-1.5">
              <Label>
                {scenarioType === "replace_product" ? "Existing product to remove" : "Product assignment"}
              </Label>
              <Select value={assignmentId} onValueChange={setAssignmentId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a deployed product assignment" />
                </SelectTrigger>
                <SelectContent>
                  {assignments.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {assignmentLabel(a.id)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {showEditionSwap && (
            <div className="flex flex-col gap-4 rounded-md border p-3">
              <div className="flex flex-col gap-1.5">
                <Label>Target Edition</Label>
                <Select
                  value={targetEditionId}
                  onValueChange={(v) => {
                    setTargetEditionId(v);
                    setTargetModuleIds(new Set());
                  }}
                  disabled={!selectedAssignment}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue
                      placeholder={selectedAssignment ? "Select target edition" : "Select an assignment first"}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {targetEditions.map((e) => (
                      <SelectItem key={e.id} value={String(e.id)}>
                        {e.name} {e.tier ? `(${e.tier})` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Modules enabled on the new edition</Label>
                <div className="flex max-h-32 flex-col gap-1 overflow-y-auto rounded-md border p-2">
                  {targetModules.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      {targetEditionId ? "No modules defined for this edition." : "Select a target edition first."}
                    </p>
                  )}
                  {targetModules.map((m) => (
                    <label key={m.id} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={targetModuleIds.has(m.id)}
                        onChange={() => toggleTargetModule(m.id)}
                        className="size-4 rounded border-input"
                      />
                      {m.name}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {showModuleToggle && (
            <div className="flex flex-col gap-1.5">
              <Label>
                Module to {scenarioType === "enable_module" ? "enable" : "disable"}
              </Label>
              <Select value={toggleModuleId} onValueChange={setToggleModuleId} disabled={!selectedAssignment}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select module" />
                </SelectTrigger>
                <SelectContent>
                  {enabledModuleOptions.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {moduleMap.get(m.id) ?? m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {showDeploymentModelField && (
            <div className="flex flex-col gap-1.5 sm:max-w-xs">
              <Label>Deployment Model</Label>
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
          )}

          {showDeploymentStatusField && (
            <div className="flex flex-col gap-1.5 sm:max-w-xs">
              <Label>New Availability / Deployment Status</Label>
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
          )}

          {showBulkAssignments && (
            <div className="flex flex-col gap-1.5">
              <Label>Product assignments to remove</Label>
              <div className="flex max-h-48 flex-col gap-1 overflow-y-auto rounded-md border p-2">
                {assignments.length === 0 && (
                  <p className="text-sm text-muted-foreground">No product assignments yet.</p>
                )}
                {assignments.map((a) => (
                  <label key={a.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={bulkAssignmentIds.has(a.id)}
                      onChange={() => toggleBulkAssignment(a.id)}
                      className="size-4 rounded border-input"
                    />
                    {assignmentLabel(a.id)}
                  </label>
                ))}
              </div>
            </div>
          )}

          {formError && <p className="text-sm text-destructive">{formError}</p>}
          <div>
            <Button onClick={handleRunSimulation} disabled={simulateMutation.isPending}>
              <FlaskConical className="size-4" />
              {simulateMutation.isPending ? "Simulating..." : "Run Simulation"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {report && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg font-semibold tracking-tight">
              Results: {report.name || SCENARIO_TYPE_LABELS[report.scenario_type]}
            </h3>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("json")}
                disabled={exportingFormat !== null}
              >
                <Download className="size-4" /> {exportingFormat === "json" ? "Exporting..." : "JSON"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("excel")}
                disabled={exportingFormat !== null}
              >
                <Download className="size-4" /> {exportingFormat === "excel" ? "Exporting..." : "Excel"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("pdf")}
                disabled={exportingFormat !== null}
              >
                <Download className="size-4" /> {exportingFormat === "pdf" ? "Exporting..." : "PDF"}
              </Button>
            </div>
          </div>

          {/* Executive Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Executive Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-1.5 text-sm">
                {report.executive_summary.map((line, index) => (
                  <li key={index}>{line}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Current vs Proposed metric grid */}
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
            {deltaFields.map(({ key, label }) => {
              const delta = report[key] as SimulationReport["coverage_delta"];
              return (
                <Card key={String(key)}>
                  <CardHeader>
                    <CardDescription>{label}</CardDescription>
                    <CardTitle className="text-xl">
                      {delta.current_value} <span className="text-muted-foreground">&rarr;</span>{" "}
                      {delta.proposed_value}
                    </CardTitle>
                    <div className="pt-1">{classificationBadge(delta.classification)}</div>
                  </CardHeader>
                </Card>
              );
            })}
          </div>

          {/* Before/After chart */}
          <Card>
            <CardHeader>
              <CardTitle>Current vs Proposed</CardTitle>
              <CardDescription>
                Score-scale metrics compared side by side (all 0-100).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={percentChartData} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis allowDecimals={false} width={30} />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="Current" fill="#64748b" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Proposed" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Domain coverage heatmaps */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Current Coverage Heatmap</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {report.current_coverage.domain_coverage.map((d) => (
                    <div
                      key={d.domain_id}
                      className="flex flex-col gap-1 rounded-md p-3 text-xs"
                      style={heatStyle(d.coverage_percentage)}
                    >
                      <span className="font-medium leading-tight">{d.domain_name}</span>
                      <span className="text-lg font-semibold">{d.coverage_percentage}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Proposed Coverage Heatmap</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {report.proposed_coverage.domain_coverage.map((d) => (
                    <div
                      key={d.domain_id}
                      className="flex flex-col gap-1 rounded-md p-3 text-xs"
                      style={heatStyle(d.coverage_percentage)}
                    >
                      <span className="font-medium leading-tight">{d.domain_name}</span>
                      <span className="text-lg font-semibold">{d.coverage_percentage}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Vendor Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Vendor Comparison</CardTitle>
              <CardDescription>Vendors whose footprint changed under this scenario.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Vendor</TableHead>
                      <TableHead className="text-right">Current Caps</TableHead>
                      <TableHead className="text-right">Proposed Caps</TableHead>
                      <TableHead className="text-right">Current License Qty</TableHead>
                      <TableHead className="text-right">Proposed License Qty</TableHead>
                      <TableHead>Classification</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.vendor_comparison.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No vendor-level changes.
                        </TableCell>
                      </TableRow>
                    )}
                    {report.vendor_comparison.map((v) => (
                      <TableRow key={v.vendor}>
                        <TableCell>{v.vendor}</TableCell>
                        <TableCell className="text-right">{v.current_capability_count}</TableCell>
                        <TableCell className="text-right">{v.proposed_capability_count}</TableCell>
                        <TableCell className="text-right">{v.current_license_quantity}</TableCell>
                        <TableCell className="text-right">{v.proposed_license_quantity}</TableCell>
                        <TableCell>{classificationBadge(v.classification)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Framework Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Framework Comparison</CardTitle>
              <CardDescription>Compliance controls satisfied, current vs proposed.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-80 overflow-y-auto overflow-x-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Framework</TableHead>
                      <TableHead className="text-right">Total Controls</TableHead>
                      <TableHead className="text-right">Current Satisfied</TableHead>
                      <TableHead className="text-right">Proposed Satisfied</TableHead>
                      <TableHead>Classification</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.framework_comparison.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground">
                          No framework-mapped capabilities.
                        </TableCell>
                      </TableRow>
                    )}
                    {report.framework_comparison.map((f) => (
                      <TableRow key={`${f.framework_name}-${f.framework_version}`}>
                        <TableCell>
                          {f.framework_name} v{f.framework_version}
                        </TableCell>
                        <TableCell className="text-right">{f.total_controls}</TableCell>
                        <TableCell className="text-right">{f.current_satisfied_controls}</TableCell>
                        <TableCell className="text-right">{f.proposed_satisfied_controls}</TableCell>
                        <TableCell>{classificationBadge(f.classification)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Capability Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Capability Comparison</CardTitle>
              <CardDescription>Every capability whose coverage status changed.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="max-h-96 overflow-y-auto overflow-x-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Domain</TableHead>
                      <TableHead>Current</TableHead>
                      <TableHead>Proposed</TableHead>
                      <TableHead>Classification</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.capability_comparison.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">
                          No capability status changes.
                        </TableCell>
                      </TableRow>
                    )}
                    {report.capability_comparison.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="font-mono text-xs">{c.code}</TableCell>
                        <TableCell>{c.name}</TableCell>
                        <TableCell>{c.domain_name}</TableCell>
                        <TableCell>
                          <Badge variant={c.current_covered ? "default" : "outline"}>
                            {c.current_covered ? "Covered" : "Missing"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={c.proposed_covered ? "default" : "outline"}>
                            {c.proposed_covered ? "Covered" : "Missing"}
                          </Badge>
                        </TableCell>
                        <TableCell>{classificationBadge(c.classification)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
