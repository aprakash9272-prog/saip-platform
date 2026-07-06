"use client";

import { Eye, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { ColumnConfig, EntityRecord, ReferenceMaps } from "./types";
import { getFieldValue } from "./types";

interface DataTableProps<T extends EntityRecord> {
  columns: ColumnConfig<T>[];
  rows: T[];
  referenceMaps: ReferenceMaps;
  loading?: boolean;
  onView: (item: T) => void;
  onEdit: (item: T) => void;
  onDelete: (item: T) => void;
  getRowId: (item: T) => number;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export function DataTable<T extends EntityRecord>({
  columns,
  rows,
  referenceMaps,
  loading,
  onView,
  onEdit,
  onDelete,
  getRowId,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col) => (
              <TableHead key={col.key}>{col.header}</TableHead>
            ))}
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading && (
            <TableRow>
              <TableCell
                colSpan={columns.length + 1}
                className="text-center text-muted-foreground"
              >
                Loading...
              </TableCell>
            </TableRow>
          )}
          {!loading && rows.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={columns.length + 1}
                className="text-center text-muted-foreground"
              >
                No records found.
              </TableCell>
            </TableRow>
          )}
          {!loading &&
            rows.map((row) => (
              <TableRow key={getRowId(row)}>
                {columns.map((col) => (
                  <TableCell key={col.key}>
                    {col.render
                      ? col.render(row, referenceMaps)
                      : formatCell(getFieldValue(row, col.key))}
                  </TableCell>
                ))}
                <TableCell className="flex justify-end gap-1 text-right">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => onView(row)}
                    aria-label="View details"
                  >
                    <Eye className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => onEdit(row)}
                    aria-label="Edit"
                  >
                    <Pencil className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => onDelete(row)}
                    aria-label="Delete"
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
        </TableBody>
      </Table>
    </div>
  );
}
