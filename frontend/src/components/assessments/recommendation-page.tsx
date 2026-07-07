"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpDown, Download, TrendingUp } from "lucide-react";
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
import { downloadRecommendationExport, getRecommendationReport } from "@/lib/api/resources";
import type { RecommendationExportFormat, RecommendationItem } from "@/lib/api/types";
import { PRIORITY_LEVELS } from "@/lib/api/types";

const PRIORITY_COLORS: Record<string, string> = {
  Critical: "#991b1b",
  High: "#dc2626",
  Medium: "#d97706",
  Low: "#6b7280",
};

const PRIORITY_BADGE_CLASS: Record<string, string> = {
  Critical: "bg-red-900 text-white dark:bg-red-900 dark:text-white",
  High: "bg-red-600 text-white dark:bg-red-600 dark:text-white",
  Medium: "bg-amber-600 text-white dark:bg-amber-600 dark:text-white",
  Low: "bg-gray-500 text-white dark:bg-gray-500 dark:text-white",
};

const ALL = "__all__";

type SortColumn =
  | "capability_code"
  | "domain_name"
  | "priority"
  | "confidence"
  | "estimated_risk_reduction";

function priorityRank(priority: string): number {
  const index = PRIORITY_LEVELS.indexOf(priority as (typeof PRIORITY_LEVELS)[number]);
  return index === -1 ? PRIORITY_LEVELS.length : index;
}

interface RecommendationPageProps {
  projectId: number;
}

export function RecommendationPage({ projectId }: RecommendationPageProps) {
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>(ALL);
  const [domainFilter, setDomainFilter] = useState<string>(ALL);
  const [sortColumn, setSortColumn] = useState<SortColumn>("priority");
  const [sortDesc, setSortDesc] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<RecommendationExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["analysis", "recommendations", projectId],
    queryFn: () => getRecommendationReport(projectId),
  });

  const report = query.data;

  const domainOptions = useMemo(
    () =>
      Array.from(new Set((report?.recommendations ?? []).map((r) => r.domain_name))).sort(
        (a, b) => a.localeCompare(b),
      ),
    [report],
  );

  const filteredRecommendations = useMemo(() => {
    if (!report) return [];
    const term = search.trim().toLowerCase();
    let items = report.recommendations.filter((rec) => {
      if (priorityFilter !== ALL && rec.priority !== priorityFilter) return false;
      if (domainFilter !== ALL && rec.domain_name !== domainFilter) return false;
      if (
        term &&
        !rec.capability_code.toLowerCase().includes(term) &&
        !rec.capability_name.toLowerCase().includes(term)
      ) {
        return false;
      }
      return true;
    });
    items = [...items].sort((a, b) => {
      let cmp = 0;
      if (sortColumn === "priority") {
        cmp = priorityRank(a.priority) - priorityRank(b.priority);
      } else if (sortColumn === "confidence") {
        cmp = a.candidates[0].confidence_score - b.candidates[0].confidence_score;
      } else if (sortColumn === "estimated_risk_reduction") {
        cmp = a.estimated_risk_reduction - b.estimated_risk_reduction;
      } else {
        cmp = String(a[sortColumn]).localeCompare(String(b[sortColumn]));
      }
      return sortDesc ? -cmp : cmp;
    });
    return items;
  }, [report, search, priorityFilter, domainFilter, sortColumn, sortDesc]);

  const toggleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDesc((prev) => !prev);
    } else {
      setSortColumn(column);
      setSortDesc(false);
    }
  };

  const priorityBarData = useMemo(
    () =>
      report
        ? [
            { name: "Critical", count: report.critical_priority_count },
            { name: "High", count: report.high_priority_count },
            { name: "Medium", count: report.medium_priority_count },
            { name: "Low", count: report.low_priority_count },
          ]
        : [],
    [report],
  );

  const topRecommendations = useMemo(
    () =>
      (report?.recommendations ?? [])
        .filter((r) => r.priority === "Critical" || r.priority === "High")
        .slice(0, 6),
    [report],
  );

  const handleExport = async (format: RecommendationExportFormat) => {
    setExportError(null);
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadRecommendationExport(projectId, format);
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
    return <p className="text-sm text-muted-foreground">Loading recommendations...</p>;
  }
  if (query.isError || !report) {
    return <p className="text-sm text-destructive">Failed to load recommendations.</p>;
  }

  const forecast = report.coverage_forecast;

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
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">Recommendations</h2>
          <p className="text-xs text-muted-foreground">
            Deterministic, knowledge-base-driven recommendations to close every addressable
            gap — no AI or LLM reasoning. Gaps with no known catalog product are excluded.
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
            <CardDescription>Estimated Risk Reduction</CardDescription>
            <CardTitle className="flex items-center gap-2 text-4xl text-emerald-600 dark:text-emerald-400">
              <TrendingUp className="size-7" /> {report.estimated_overall_risk_reduction}
            </CardTitle>
            <Badge variant="secondary" className="w-fit">
              {report.current_risk_score} &rarr; {report.projected_risk_score}
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
            <CardDescription>Addressable</CardDescription>
            <CardTitle className="text-3xl text-emerald-600 dark:text-emerald-400">
              {report.addressable_gaps}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Unaddressable</CardDescription>
            <CardTitle className="text-3xl text-muted-foreground">
              {report.unaddressable_gaps}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Critical Priority</CardDescription>
            <CardTitle className="text-3xl" style={{ color: PRIORITY_COLORS.Critical }}>
              {report.critical_priority_count}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>High Priority</CardDescription>
            <CardTitle className="text-3xl" style={{ color: PRIORITY_COLORS.High }}>
              {report.high_priority_count}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Coverage Improvement Forecast */}
      <Card>
        <CardHeader>
          <CardTitle>Coverage Improvement Forecast</CardTitle>
          <CardDescription>
            Projected capability coverage if every addressable gap&apos;s top recommendation is implemented.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <div>
              <p className="text-xs text-muted-foreground">Current</p>
              <p className="text-3xl font-semibold">{forecast.current_coverage_percentage}%</p>
            </div>
            <div className="flex-1">
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-emerald-500/40"
                  style={{ width: `${forecast.projected_coverage_percentage}%` }}
                />
                <div
                  className="-mt-3 h-full rounded-full bg-emerald-500"
                  style={{ width: `${forecast.current_coverage_percentage}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {forecast.addressable_gap_count} addressable &middot; {forecast.unaddressable_gap_count} unaddressable
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Projected</p>
              <p className="text-3xl font-semibold text-emerald-600 dark:text-emerald-400">
                {forecast.projected_coverage_percentage}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Recommendations */}
      {topRecommendations.length > 0 && (
        <div>
          <h3 className="mb-2 text-lg font-semibold tracking-tight">
            Top Recommendations ({topRecommendations.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {topRecommendations.map((rec) => {
              const best = rec.candidates[0];
              return (
                <Card key={rec.capability_id} className="border-red-900/30">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-muted-foreground">
                        {rec.capability_code}
                      </span>
                      <Badge className={PRIORITY_BADGE_CLASS[rec.priority]}>{rec.priority}</Badge>
                    </div>
                    <CardTitle className="text-base">{rec.capability_name}</CardTitle>
                    <CardDescription>
                      {best.vendor} &middot; {best.product} ({best.module})
                    </CardDescription>
                    <p className="text-xs text-muted-foreground">
                      Confidence {best.confidence_score} &middot; {best.implementation_complexity} complexity &middot;{" "}
                      {best.estimated_effort}
                    </p>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Priority Matrix */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Priority Matrix</CardTitle>
            <CardDescription>Recommendation count by priority tier.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={priorityBarData} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} width={30} />
                  <RechartsTooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {priorityBarData.map((entry) => (
                      <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Product Comparison</CardTitle>
            <CardDescription>Catalog products by number of gaps they address.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-56 overflow-y-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead className="text-right">Gaps</TableHead>
                    <TableHead className="text-right">Avg Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.product_comparison.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground">
                        No products address any gap.
                      </TableCell>
                    </TableRow>
                  )}
                  {report.product_comparison.map((entry) => (
                    <TableRow key={`${entry.vendor}-${entry.product}`}>
                      <TableCell>{entry.vendor}</TableCell>
                      <TableCell>{entry.product}</TableCell>
                      <TableCell className="text-right">{entry.gaps_addressed}</TableCell>
                      <TableCell className="text-right">{entry.average_confidence_score}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendation Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Recommendations</CardTitle>
          <CardDescription>Every addressable gap, searchable, filterable, and sortable.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Search by code or name..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="max-w-xs"
            />
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="All priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All priorities</SelectItem>
                {PRIORITY_LEVELS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p}
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
              {filteredRecommendations.length} of {report.recommendations.length} recommendations
            </span>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {(
                    [
                      ["capability_code", "Capability"],
                      ["domain_name", "Domain"],
                      ["priority", "Priority"],
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
                  <TableHead>Best Product</TableHead>
                  <TableHead>License Tier</TableHead>
                  <TableHead>Deployment</TableHead>
                  <TableHead>
                    <button
                      type="button"
                      className="flex items-center gap-1 hover:text-foreground"
                      onClick={() => toggleSort("confidence")}
                    >
                      Confidence
                      <ArrowUpDown className="size-3" />
                    </button>
                  </TableHead>
                  <TableHead>Complexity</TableHead>
                  <TableHead>Effort</TableHead>
                  <TableHead>
                    <button
                      type="button"
                      className="flex items-center gap-1 hover:text-foreground"
                      onClick={() => toggleSort("estimated_risk_reduction")}
                    >
                      Risk Reduction
                      <ArrowUpDown className="size-3" />
                    </button>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRecommendations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={10} className="text-center text-muted-foreground">
                      No recommendations match these filters.
                    </TableCell>
                  </TableRow>
                )}
                {filteredRecommendations.map((rec: RecommendationItem) => {
                  const best = rec.candidates[0];
                  return (
                    <TableRow key={rec.capability_id}>
                      <TableCell className="font-mono text-xs">{rec.capability_code}</TableCell>
                      <TableCell>{rec.domain_name}</TableCell>
                      <TableCell>
                        <Badge className={PRIORITY_BADGE_CLASS[rec.priority]}>{rec.priority}</Badge>
                      </TableCell>
                      <TableCell title={`${rec.candidates.length} candidate(s)`}>
                        {best.vendor} - {best.product}
                      </TableCell>
                      <TableCell>{best.licensing_tier ?? "—"}</TableCell>
                      <TableCell>{best.deployment_model}</TableCell>
                      <TableCell>{best.confidence_score}</TableCell>
                      <TableCell>{best.implementation_complexity}</TableCell>
                      <TableCell>{best.estimated_effort}</TableCell>
                      <TableCell>{rec.estimated_risk_reduction}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
