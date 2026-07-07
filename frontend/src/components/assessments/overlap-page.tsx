"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpDown, Download } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
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
import { downloadOverlapExport, getOverlapReport } from "@/lib/api/resources";
import type { DuplicateCapabilityOverlap, OverlapExportFormat } from "@/lib/api/types";

const ALL = "__all__";

function heatStyle(pct: number): React.CSSProperties {
  // 0% overlap -> green (good), 100% overlap -> red (bad, fully redundant).
  const hue = Math.max(0, Math.min(120, 120 - (pct / 100) * 120));
  return { backgroundColor: `hsl(${hue}, 70%, 45%)`, color: "white" };
}

function matrixCellStyle(count: number, max: number): React.CSSProperties {
  if (count === 0 || max === 0) return {};
  const intensity = 0.15 + (count / max) * 0.55;
  return { backgroundColor: `rgba(220, 38, 38, ${intensity})` };
}

function scoreColor(score: number, invert = false): string {
  const good = invert ? score <= 30 : score >= 70;
  const bad = invert ? score >= 70 : score <= 30;
  if (good) return "text-emerald-600 dark:text-emerald-400";
  if (bad) return "text-red-600 dark:text-red-400";
  return "text-amber-600 dark:text-amber-400";
}

type SortColumn = "code" | "domain_name" | "provider_count";

interface OverlapPageProps {
  projectId: number;
}

export function OverlapPage({ projectId }: OverlapPageProps) {
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState<string>(ALL);
  const [vendorFilterOnly, setVendorFilterOnly] = useState<string>(ALL);
  const [sortColumn, setSortColumn] = useState<SortColumn>("provider_count");
  const [sortDesc, setSortDesc] = useState(true);
  const [exportingFormat, setExportingFormat] = useState<OverlapExportFormat | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["analysis", "overlap", projectId],
    queryFn: () => getOverlapReport(projectId),
  });

  const report = query.data;

  const domainOptions = useMemo(
    () =>
      Array.from(new Set((report?.duplicate_capabilities ?? []).map((d) => d.domain_name))).sort(
        (a, b) => a.localeCompare(b),
      ),
    [report],
  );

  const filteredDuplicates = useMemo(() => {
    if (!report) return [];
    const term = search.trim().toLowerCase();
    let items = report.duplicate_capabilities.filter((dup) => {
      if (domainFilter !== ALL && dup.domain_name !== domainFilter) return false;
      if (vendorFilterOnly === "cross-vendor" && !dup.cross_vendor) return false;
      if (
        term &&
        !dup.code.toLowerCase().includes(term) &&
        !dup.name.toLowerCase().includes(term)
      ) {
        return false;
      }
      return true;
    });
    items = [...items].sort((a, b) => {
      let cmp = 0;
      if (sortColumn === "provider_count") {
        cmp = a.provider_count - b.provider_count;
      } else {
        cmp = String(a[sortColumn]).localeCompare(String(b[sortColumn]));
      }
      return sortDesc ? -cmp : cmp;
    });
    return items;
  }, [report, search, domainFilter, vendorFilterOnly, sortColumn, sortDesc]);

  const toggleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDesc((prev) => !prev);
    } else {
      setSortColumn(column);
      setSortDesc(false);
    }
  };

  const domainBarData = useMemo(
    () =>
      (report?.domain_overlap_scores ?? [])
        .filter((d) => d.duplicate_count > 0)
        .sort((a, b) => b.duplicate_count - a.duplicate_count)
        .map((d) => ({ name: d.domain_name, count: d.duplicate_count })),
    [report],
  );

  const vendorBarData = useMemo(
    () =>
      (report?.vendor_summary ?? []).map((v) => ({
        name: v.vendor,
        unique: v.unique_capabilities_provided,
        overlapping: v.overlapping_capabilities_provided,
      })),
    [report],
  );

  const productLabels = useMemo(() => {
    if (!report) return [];
    const labels = new Set<string>();
    for (const pair of report.product_overlaps) {
      labels.add(`${pair.vendor_a} - ${pair.product_a}`);
      labels.add(`${pair.vendor_b} - ${pair.product_b}`);
    }
    return Array.from(labels).sort((a, b) => a.localeCompare(b));
  }, [report]);

  const overlapMatrix = useMemo(() => {
    const matrix = new Map<string, number>();
    let max = 0;
    for (const pair of report?.product_overlaps ?? []) {
      const a = `${pair.vendor_a} - ${pair.product_a}`;
      const b = `${pair.vendor_b} - ${pair.product_b}`;
      matrix.set(`${a}|${b}`, pair.shared_capability_count);
      matrix.set(`${b}|${a}`, pair.shared_capability_count);
      max = Math.max(max, pair.shared_capability_count);
    }
    return { matrix, max };
  }, [report]);

  const handleExport = async (format: OverlapExportFormat) => {
    setExportError(null);
    setExportingFormat(format);
    try {
      const { blob, filename } = await downloadOverlapExport(projectId, format);
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
    return <p className="text-sm text-muted-foreground">Loading overlap analysis...</p>;
  }
  if (query.isError || !report) {
    return <p className="text-sm text-destructive">Failed to load overlap analysis.</p>;
  }

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
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">Overlap &amp; Optimization</h2>
          <p className="text-xs text-muted-foreground">
            Deterministic detection of duplicate capabilities, redundant products, and
            consolidation opportunities across deployed products — no AI reasoning.
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
        <Card>
          <CardHeader>
            <CardDescription>Optimization Score</CardDescription>
            <CardTitle className={`text-3xl ${scoreColor(report.optimization_score)}`}>
              {report.optimization_score}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Overlap %</CardDescription>
            <CardTitle className={`text-3xl ${scoreColor(report.overlap_percentage, true)}`}>
              {report.overlap_percentage}%
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Vendor Consolidation</CardDescription>
            <CardTitle className={`text-3xl ${scoreColor(report.vendor_consolidation_score, true)}`}>
              {report.vendor_consolidation_score}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>License Reduction Opp.</CardDescription>
            <CardTitle className="text-3xl">{report.license_reduction_opportunity}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Cost Optimization</CardDescription>
            <CardTitle className={`text-3xl ${scoreColor(report.cost_optimization_score, true)}`}>
              {report.cost_optimization_score}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Operational Complexity</CardDescription>
            <CardTitle className={`text-3xl ${scoreColor(report.operational_complexity_score, true)}`}>
              {report.operational_complexity_score}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Duplicate / Cross-Vendor</CardDescription>
            <CardTitle className="text-3xl">
              {report.duplicate_capability_count}
              <span className="text-base text-muted-foreground"> / {report.cross_vendor_duplicate_count}</span>
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Duplicate Capabilities by Domain</CardTitle>
            <CardDescription>Domains with the most redundant coverage.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={domainBarData} layout="vertical" margin={{ left: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 10 }} />
                  <RechartsTooltip />
                  <Bar dataKey="count" fill="#dc2626" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Unique vs. Overlapping Capabilities by Vendor</CardTitle>
            <CardDescription>How much of each vendor&apos;s footprint is redundant.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={vendorBarData} margin={{ top: 8, right: 8, left: -20, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} width={30} />
                  <RechartsTooltip />
                  <Bar dataKey="unique" stackId="a" fill="#16a34a" name="Unique" />
                  <Bar dataKey="overlapping" stackId="a" fill="#dc2626" name="Overlapping" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Capability Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle>Capability Heatmap</CardTitle>
          <CardDescription>Overlap percentage of covered capabilities, per domain.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {report.domain_overlap_scores.map((domain) => (
              <div
                key={domain.domain_id}
                className="flex flex-col gap-1 rounded-md p-3 text-xs"
                style={heatStyle(domain.overlap_percentage)}
              >
                <span className="font-medium leading-tight">{domain.domain_name}</span>
                <span className="text-lg font-semibold">{domain.overlap_percentage}%</span>
                <span className="opacity-90">
                  {domain.duplicate_count} / {domain.covered_count} covered
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Vendor Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Vendor Comparison</CardTitle>
          <CardDescription>Deployed footprint, redundancy, and open-gap value per vendor.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor</TableHead>
                  <TableHead className="text-right">Products</TableHead>
                  <TableHead className="text-right">Total Caps</TableHead>
                  <TableHead className="text-right">Unique</TableHead>
                  <TableHead className="text-right">Overlapping</TableHead>
                  <TableHead className="text-right">License Qty</TableHead>
                  <TableHead className="text-right">Open Gaps Addressable</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.vendor_summary.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      No deployed vendors.
                    </TableCell>
                  </TableRow>
                )}
                {report.vendor_summary.map((v) => (
                  <TableRow key={v.vendor}>
                    <TableCell>{v.vendor}</TableCell>
                    <TableCell className="text-right">{v.deployed_product_count}</TableCell>
                    <TableCell className="text-right">{v.total_capabilities_provided}</TableCell>
                    <TableCell className="text-right text-emerald-600 dark:text-emerald-400">
                      {v.unique_capabilities_provided}
                    </TableCell>
                    <TableCell className="text-right text-red-600 dark:text-red-400">
                      {v.overlapping_capabilities_provided}
                    </TableCell>
                    <TableCell className="text-right">{v.total_license_quantity}</TableCell>
                    <TableCell className="text-right">{v.open_gaps_addressable}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Overlap Matrix */}
      {productLabels.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Overlap Matrix</CardTitle>
            <CardDescription>Shared capability count between every pair of deployed products.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    {productLabels.map((label) => (
                      <TableHead key={label} className="text-center text-xs">
                        {label}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {productLabels.map((rowLabel) => (
                    <TableRow key={rowLabel}>
                      <TableCell className="text-xs font-medium">{rowLabel}</TableCell>
                      {productLabels.map((colLabel) => {
                        if (rowLabel === colLabel) {
                          return (
                            <TableCell key={colLabel} className="text-center text-muted-foreground">
                              —
                            </TableCell>
                          );
                        }
                        const count = overlapMatrix.matrix.get(`${rowLabel}|${colLabel}`) ?? 0;
                        return (
                          <TableCell
                            key={colLabel}
                            className="text-center text-xs"
                            style={matrixCellStyle(count, overlapMatrix.max)}
                          >
                            {count || "—"}
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
      )}

      {/* Duplicate Products */}
      <Card>
        <CardHeader>
          <CardTitle>Duplicate Products (License Reduction Candidates)</CardTitle>
          <CardDescription>
            Deployed products whose capabilities are wholly or partially covered elsewhere.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Edition</TableHead>
                  <TableHead className="text-right">License Qty</TableHead>
                  <TableHead className="text-right">Redundancy %</TableHead>
                  <TableHead>Fully Redundant</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.redundant_licenses.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      No redundant products identified.
                    </TableCell>
                  </TableRow>
                )}
                {report.redundant_licenses.map((r) => (
                  <TableRow key={r.assignment_id}>
                    <TableCell>{r.vendor}</TableCell>
                    <TableCell>{r.product}</TableCell>
                    <TableCell>{r.edition}</TableCell>
                    <TableCell className="text-right">{r.license_quantity ?? "—"}</TableCell>
                    <TableCell className="text-right">{r.redundancy_percentage}%</TableCell>
                    <TableCell>
                      {r.fully_redundant ? (
                        <Badge className="bg-red-600 text-white dark:bg-red-600 dark:text-white">
                          Fully Redundant
                        </Badge>
                      ) : (
                        <Badge variant="outline">Partial</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Optimization Opportunities */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Opportunities: Unused Capabilities</CardTitle>
          <CardDescription>
            Capabilities available under a deployed edition&apos;s license but never enabled — purchased but unused.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-80 overflow-y-auto overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Module</TableHead>
                  <TableHead>Capability</TableHead>
                  <TableHead>Domain</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.unused_capabilities.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      No unused capabilities — every enabled edition is fully utilized.
                    </TableCell>
                  </TableRow>
                )}
                {report.unused_capabilities.map((u, index) => (
                  <TableRow key={`${u.assignment_id}-${u.capability_code}-${index}`}>
                    <TableCell>{u.vendor}</TableCell>
                    <TableCell>{u.product}</TableCell>
                    <TableCell>{u.module}</TableCell>
                    <TableCell>
                      {u.capability_code} — {u.capability_name}
                    </TableCell>
                    <TableCell>{u.domain_name}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Duplicate Capabilities Table (search/filter/sort) */}
      <Card>
        <CardHeader>
          <CardTitle>Duplicate Capabilities</CardTitle>
          <CardDescription>Every covered capability provided by more than one deployed product.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Search by code or name..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="max-w-xs"
            />
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
            <Select value={vendorFilterOnly} onValueChange={setVendorFilterOnly}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All duplicates" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All duplicates</SelectItem>
                <SelectItem value="cross-vendor">Cross-vendor only</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-xs text-muted-foreground">
              {filteredDuplicates.length} of {report.duplicate_capabilities.length} duplicates
            </span>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {(
                    [
                      ["code", "Code"],
                      ["domain_name", "Domain"],
                      ["provider_count", "Providers"],
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
                  <TableHead>Name</TableHead>
                  <TableHead>Vendors</TableHead>
                  <TableHead>Cross-Vendor</TableHead>
                  <TableHead>Providers</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDuplicates.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      No duplicate capabilities match these filters.
                    </TableCell>
                  </TableRow>
                )}
                {filteredDuplicates.map((dup: DuplicateCapabilityOverlap) => (
                  <TableRow key={dup.id}>
                    <TableCell className="font-mono text-xs">{dup.code}</TableCell>
                    <TableCell>{dup.domain_name}</TableCell>
                    <TableCell>{dup.provider_count}</TableCell>
                    <TableCell>{dup.name}</TableCell>
                    <TableCell>{dup.distinct_vendor_count}</TableCell>
                    <TableCell>
                      {dup.cross_vendor ? (
                        <Badge className="bg-red-600 text-white dark:bg-red-600 dark:text-white">Yes</Badge>
                      ) : (
                        <Badge variant="outline">No</Badge>
                      )}
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-xs" title={dup.providers.join(", ")}>
                      {dup.providers.join(", ")}
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
