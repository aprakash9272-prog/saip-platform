"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpDown, Download } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
import { downloadGapExport, getGapReport } from "@/lib/api/resources";
import type { GapExportFormat, GapItem } from "@/lib/api/types";
import { SEVERITY_LEVELS } from "@/lib/api/types";

const SEVERITY_COLORS: Record<string, string> = {
  Critical: "#991b1b",
  High: "#dc2626",
  Medium: "#d97706",
  Low: "#ca8a04",
  Informational: "#6b7280",
};

const SEVERITY_BADGE_CLASS: Record<string, string> = {
  Critical: "bg-red-900 text-white dark:bg-red-900 dark:text-white",
  High: "bg-red-600 text-white dark:bg-red-600 dark:text-white",
  Medium: "bg-amber-600 text-white dark:bg-amber-600 dark:text-white",
  Low: "bg-yellow-600 text-white dark:bg-yellow-600 dark:text-white",
  Informational: "bg-gray-500 text-white dark:bg-gray-500 dark:text-white",
};

const BUSINESS_IMPACT_LEVELS = ["Severe", "High", "Moderate", "Low"] as const;

const ALL = "__all__";

function riskHeatStyle(riskScore: number): React.CSSProperties {
  // 0 risk -> green, 100 risk -> red (inverse of a coverage heatmap).
  const hue = Math.max(0, Math.min(120, 120 - (riskScore / 100) * 120));
  return { backgroundColor: `hsl(${hue}, 70%, 45%)`, color: "white" };
}

type SortColumn = "code" | "name" | "domain_name" | "severity" | "business_impact";

function severityRank(severity: string): number {
  const index = SEVERITY_LEVELS.indexOf(severity as (typeof SEVERITY_LEVELS)[number]);
  return index === -1 ? SEVERITY_LEVELS.length : index;
}

interface GapAnalysisPageProps {
  projectId: number;
}

export function GapAnalysisPage({ projectId }: GapAnalysisPageProps) {
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>(ALL);
  const [domainFilter, setDomainFilter] = useState<string>(ALL);
  const [sortColumn, setSortColumn] = useState<SortColumn>("severity");
  const [sortDesc, setSortDesc] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<GapExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["analysis", "gaps", projectId],
    queryFn: () => getGapReport(projectId),
  });

  const report = query.data;

  const domainOptions = useMemo(
    () =>
      Array.from(new Set((report?.gaps ?? []).map((g) => g.domain_name))).sort((a, b) =>
        a.localeCompare(b),
      ),
    [report],
  );

  const filteredGaps = useMemo(() => {
    if (!report) return [];
    const term = search.trim().toLowerCase();
    let items = report.gaps.filter((gap) => {
      if (severityFilter !== ALL && gap.severity !== severityFilter) return false;
      if (domainFilter !== ALL && gap.domain_name !== domainFilter) return false;
      if (term && !gap.code.toLowerCase().includes(term) && !gap.name.toLowerCase().includes(term)) {
        return false;
      }
      return true;
    });
    items = [...items].sort((a, b) => {
      let cmp = 0;
      if (sortColumn === "severity") {
        cmp = severityRank(a.severity) - severityRank(b.severity);
      } else {
        cmp = String(a[sortColumn]).localeCompare(String(b[sortColumn]));
      }
      return sortDesc ? -cmp : cmp;
    });
    return items;
  }, [report, search, severityFilter, domainFilter, sortColumn, sortDesc]);

  const toggleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDesc((prev) => !prev);
    } else {
      setSortColumn(column);
      setSortDesc(false);
    }
  };

  const riskMatrix = useMemo(() => {
    const matrix = new Map<string, number>();
    for (const gap of report?.gaps ?? []) {
      const key = `${gap.severity}|${gap.business_impact}`;
      matrix.set(key, (matrix.get(key) ?? 0) + 1);
    }
    return matrix;
  }, [report]);

  const severityBarData = useMemo(
    () =>
      report
        ? [
            { name: "Critical", count: report.critical_count },
            { name: "High", count: report.high_count },
            { name: "Medium", count: report.medium_count },
            { name: "Low", count: report.low_count },
            { name: "Informational", count: report.informational_count },
          ]
        : [],
    [report],
  );

  const domainBarData = useMemo(
    () =>
      (report?.domain_gap_scores ?? [])
        .filter((d) => d.missing_count > 0)
        .sort((a, b) => b.missing_count - a.missing_count)
        .map((d) => ({ name: d.domain_name, count: d.missing_count })),
    [report],
  );

  const handleExport = async (format: GapExportFormat) => {
    setExportError(null);
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadGapExport(projectId, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError(`Failed to export as ${format}.`);
    } finally {
      setExportingFormat(null);
    }
  };

  if (query.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading gap analysis...</p>;
  }
  if (query.isError || !report) {
    return <p className="text-sm text-destructive">Failed to load gap analysis.</p>;
  }

  const criticalGaps = report.gaps.filter((g) => g.severity === "Critical");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <Link
            href={`/assessments/${projectId}`}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:underline"
          >
            <ArrowLeft className="size-3.5" /> {report.assessment_project_name}
          </Link>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">Gap Analysis</h2>
          <p className="text-xs text-muted-foreground">
            Every missing capability, classified by severity and business impact. Identification
            and classification only — no remediation recommendations yet.
          </p>
        </div>
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

      {exportError && <p className="text-sm text-destructive">{exportError}</p>}

      {/* Executive Summary */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-7">
        <Card className="col-span-2">
          <CardHeader>
            <CardDescription>Overall Risk Score</CardDescription>
            <CardTitle className="text-4xl">{report.overall_risk_score}</CardTitle>
            <Badge variant="secondary" className="w-fit">
              {report.overall_gap_percentage}% of catalog missing
            </Badge>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Total Gaps</CardDescription>
            <CardTitle className="text-3xl">{report.total_gaps}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Critical</CardDescription>
            <CardTitle className="text-3xl" style={{ color: SEVERITY_COLORS.Critical }}>
              {report.critical_count}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>High</CardDescription>
            <CardTitle className="text-3xl" style={{ color: SEVERITY_COLORS.High }}>
              {report.high_count}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Medium</CardDescription>
            <CardTitle className="text-3xl" style={{ color: SEVERITY_COLORS.Medium }}>
              {report.medium_count}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Low / Info</CardDescription>
            <CardTitle className="text-3xl" style={{ color: SEVERITY_COLORS.Low }}>
              {report.low_count + report.informational_count}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Critical Gap Cards */}
      {criticalGaps.length > 0 && (
        <div>
          <h3 className="mb-2 text-lg font-semibold tracking-tight">
            Critical Gaps ({criticalGaps.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {criticalGaps.map((gap) => (
              <Card key={gap.id} className="border-red-900/30">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-muted-foreground">{gap.code}</span>
                    <Badge className={SEVERITY_BADGE_CLASS[gap.severity]}>{gap.severity}</Badge>
                  </div>
                  <CardTitle className="text-base">{gap.name}</CardTitle>
                  <CardDescription>
                    {gap.domain_name} &middot; {gap.business_impact} business impact
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Gaps by Severity</CardTitle>
            <CardDescription>Count of missing capabilities per severity tier.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityBarData} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} width={30} />
                  <RechartsTooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {severityBarData.map((entry) => (
                      <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Gaps by Domain</CardTitle>
            <CardDescription>Domains with at least one missing capability.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={domainBarData} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={140}
                    tick={{ fontSize: 10 }}
                  />
                  <RechartsTooltip />
                  <Bar dataKey="count" fill={SEVERITY_COLORS.High} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Domain Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle>Domain Risk Heatmap</CardTitle>
          <CardDescription>
            Blended gap percentage and severity per domain (0 = no risk, 100 = maximum risk).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {report.domain_gap_scores.map((domain) => (
              <div
                key={domain.domain_id}
                className="flex flex-col gap-1 rounded-md p-3 text-xs"
                style={riskHeatStyle(domain.domain_risk_score)}
              >
                <span className="font-medium leading-tight">{domain.domain_name}</span>
                <span className="text-lg font-semibold">{domain.domain_risk_score}</span>
                <span className="opacity-90">
                  {domain.missing_count} missing &middot; {domain.critical_gap_count} critical
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Matrix</CardTitle>
          <CardDescription>Gap count by severity (rows) and business impact (columns).</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Severity</TableHead>
                  {BUSINESS_IMPACT_LEVELS.map((impact) => (
                    <TableHead key={impact} className="text-center">
                      {impact}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {SEVERITY_LEVELS.map((severity) => (
                  <TableRow key={severity}>
                    <TableCell>
                      <Badge className={SEVERITY_BADGE_CLASS[severity]}>{severity}</Badge>
                    </TableCell>
                    {BUSINESS_IMPACT_LEVELS.map((impact) => {
                      const count = riskMatrix.get(`${severity}|${impact}`) ?? 0;
                      return (
                        <TableCell key={impact} className="text-center">
                          {count > 0 ? (
                            <span
                              className="inline-flex size-7 items-center justify-center rounded-full text-xs font-semibold text-white"
                              style={{ backgroundColor: SEVERITY_COLORS[severity] }}
                            >
                              {count}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Gap Table */}
      <Card>
        <CardHeader>
          <CardTitle>Gap Table</CardTitle>
          <CardDescription>Every missing capability, searchable, filterable, and sortable.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Search by code or name..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="max-w-xs"
            />
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="All severities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All severities</SelectItem>
                {SEVERITY_LEVELS.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={domainFilter} onValueChange={setDomainFilter}>
              <SelectTrigger className="w-56">
                <SelectValue placeholder="All domains" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All domains</SelectItem>
                {domainOptions.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="text-xs text-muted-foreground">
              {filteredGaps.length} of {report.total_gaps} gaps
            </span>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {(
                    [
                      ["code", "Code"],
                      ["name", "Name"],
                      ["domain_name", "Domain"],
                      ["severity", "Severity"],
                      ["business_impact", "Business Impact"],
                    ] as [SortColumn, string][]
                  ).map(([column, label]) => (
                    <TableHead key={column}>
                      <button
                        type="button"
                        className="flex items-center gap-1 hover:text-foreground"
                        onClick={() => toggleSort(column)}
                      >
                        {label}
                        <ArrowUpDown className="size-3" />
                      </button>
                    </TableHead>
                  ))}
                  <TableHead>Risk Category</TableHead>
                  <TableHead>Framework Controls</TableHead>
                  <TableHead>Mapped Products</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredGaps.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground">
                      No gaps match these filters.
                    </TableCell>
                  </TableRow>
                )}
                {filteredGaps.map((gap: GapItem) => (
                  <TableRow key={gap.id}>
                    <TableCell className="font-mono text-xs">{gap.code}</TableCell>
                    <TableCell>{gap.name}</TableCell>
                    <TableCell>{gap.domain_name}</TableCell>
                    <TableCell>
                      <Badge className={SEVERITY_BADGE_CLASS[gap.severity]}>{gap.severity}</Badge>
                    </TableCell>
                    <TableCell>{gap.business_impact}</TableCell>
                    <TableCell>{gap.risk_category ?? "—"}</TableCell>
                    <TableCell
                      title={gap.framework_controls
                        .map((c) => `${c.framework_name} ${c.framework_version}: ${c.control_id}`)
                        .join(", ")}
                    >
                      {gap.framework_controls.length || "—"}
                    </TableCell>
                    <TableCell title={gap.mapped_products.join(", ")}>
                      {gap.mapped_products.length || "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{gap.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
