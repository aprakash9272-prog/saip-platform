"use client";

import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { downloadCoverageExport, getCoverageReport } from "@/lib/api/resources";
import type { CoverageExportFormat } from "@/lib/api/types";

const COVERED_COLOR = "#16a34a";
const MISSING_COLOR = "#dc2626";
const DUPLICATE_COLOR = "#d97706";

function scoreBand(pct: number): { label: string; textClass: string; barClass: string } {
  if (pct >= 80) return { label: "Strong", textClass: "text-emerald-600 dark:text-emerald-400", barClass: "bg-emerald-500" };
  if (pct >= 50) return { label: "Moderate", textClass: "text-amber-600 dark:text-amber-400", barClass: "bg-amber-500" };
  return { label: "Weak", textClass: "text-red-600 dark:text-red-400", barClass: "bg-red-500" };
}

function heatCellStyle(pct: number): React.CSSProperties {
  // 0% -> red, 50% -> amber, 100% -> green, interpolated via HSL hue.
  const hue = Math.max(0, Math.min(120, (pct / 100) * 120));
  return { backgroundColor: `hsl(${hue}, 70%, 45%)`, color: "white" };
}

type MatrixView = "missing" | "duplicate" | "covered";

const MATRIX_TABS: { key: MatrixView; label: string }[] = [
  { key: "missing", label: "Missing" },
  { key: "duplicate", label: "Duplicate" },
  { key: "covered", label: "Covered" },
];

interface CoverageAnalysisSectionProps {
  projectId: number;
}

export function CoverageAnalysisSection({ projectId }: CoverageAnalysisSectionProps) {
  const [matrixView, setMatrixView] = useState<MatrixView>("missing");
  const [exportingFormat, setExportingFormat] = useState<CoverageExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["analysis", "coverage", projectId],
    queryFn: () => getCoverageReport(projectId),
  });

  const report = query.data;

  const pieData = useMemo(
    () =>
      report
        ? [
            { name: "Covered", value: report.covered_capability_count, color: COVERED_COLOR },
            { name: "Missing", value: report.missing_capability_count, color: MISSING_COLOR },
          ]
        : [],
    [report],
  );

  const barData = useMemo(
    () =>
      (report?.domain_coverage ?? []).map((d) => ({
        name: d.domain_name.replace(" & ", " &\n"),
        coverage: d.coverage_percentage,
      })),
    [report],
  );

  const handleExport = async (format: CoverageExportFormat) => {
    setExportError(null);
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadCoverageExport(projectId, format);
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
    return <p className="text-sm text-muted-foreground">Loading coverage analysis...</p>;
  }
  if (query.isError || !report) {
    return <p className="text-sm text-destructive">Failed to load coverage analysis.</p>;
  }

  const band = scoreBand(report.overall_coverage_percentage);
  const matrixItems =
    matrixView === "missing"
      ? report.missing_capabilities
      : matrixView === "duplicate"
        ? report.duplicate_capabilities
        : report.covered_capabilities;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold tracking-tight">Coverage Analysis</h3>
          <p className="text-xs text-muted-foreground">
            Calculated only from <strong>Deployed</strong> product assignments — a
            product that is not started, in progress, or decommissioned does not
            count towards coverage. No gap remediation or recommendations yet.
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

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardDescription>Coverage Score</CardDescription>
            <CardTitle className={`text-4xl ${band.textClass}`}>
              {report.overall_coverage_percentage}%
            </CardTitle>
            <Badge variant="secondary" className="w-fit">{band.label}</Badge>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Total Capabilities</CardDescription>
            <CardTitle className="text-3xl">{report.total_capabilities}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Covered</CardDescription>
            <CardTitle className="text-3xl text-emerald-600 dark:text-emerald-400">
              {report.covered_capability_count}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Missing</CardDescription>
            <CardTitle className="text-3xl text-red-600 dark:text-red-400">
              {report.missing_capability_count}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Covered vs. Missing</CardTitle>
            <CardDescription>Share of the capability catalog covered by deployed products.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 text-sm">
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full" style={{ backgroundColor: COVERED_COLOR }} />
                Covered ({report.covered_capability_count})
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full" style={{ backgroundColor: MISSING_COLOR }} />
                Missing ({report.missing_capability_count})
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Coverage by Domain</CardTitle>
            <CardDescription>Percentage of each security domain&apos;s capabilities covered.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" hide />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} width={40} />
                  <RechartsTooltip
                    formatter={(value) => [`${value}%`, "Coverage"]}
                    labelFormatter={(label) => String(label).replace("\n", " ")}
                  />
                  <Bar dataKey="coverage" radius={[4, 4, 0, 0]}>
                    {barData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={
                          entry.coverage >= 80
                            ? COVERED_COLOR
                            : entry.coverage >= 50
                              ? DUPLICATE_COLOR
                              : MISSING_COLOR
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Domain Heatmap</CardTitle>
          <CardDescription>Coverage percentage across every security domain in the catalog.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {report.domain_coverage.map((domain) => (
              <div
                key={domain.domain_id}
                className="flex flex-col gap-1 rounded-md p-3 text-xs"
                style={heatCellStyle(domain.coverage_percentage)}
              >
                <span className="font-medium leading-tight">{domain.domain_name}</span>
                <span className="text-lg font-semibold">{domain.coverage_percentage}%</span>
                <span className="opacity-90">
                  {domain.covered_count} / {domain.total_count}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Capability Matrix</CardTitle>
            <CardDescription>Every capability in the catalog, by coverage status.</CardDescription>
          </div>
          <div className="flex gap-1">
            {MATRIX_TABS.map((tab) => (
              <Button
                key={tab.key}
                size="sm"
                variant={matrixView === tab.key ? "secondary" : "outline"}
                onClick={() => setMatrixView(tab.key)}
              >
                {tab.label} (
                {tab.key === "missing"
                  ? report.missing_capability_count
                  : tab.key === "duplicate"
                    ? report.duplicate_capability_count
                    : report.covered_capability_count}
                )
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead>Providers</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {matrixItems.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No capabilities in this category.
                    </TableCell>
                  </TableRow>
                )}
                {matrixItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-xs">{item.code}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.domain_name}</TableCell>
                    <TableCell>
                      {item.providers.length === 0 ? "—" : item.providers.join(", ")}
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
