"use client";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

import type { EntityRecord, ReferenceMaps, ResourceConfig } from "./types";
import { getFieldValue } from "./types";

interface EntityDetailSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: ResourceConfig;
  item: EntityRecord | null;
  referenceMaps: ReferenceMaps;
}

function singular(title: string): string {
  return title.endsWith("s") ? title.slice(0, -1) : title;
}

function formatValue(value: unknown): React.ReactNode {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  return String(value);
}

function formatDate(value?: string): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 border-b pb-3 last:border-none">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="text-sm">{value}</span>
    </div>
  );
}

export function EntityDetailSheet({
  open,
  onOpenChange,
  config,
  item,
  referenceMaps,
}: EntityDetailSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{singular(config.title)} details</SheetTitle>
          <SheetDescription>{config.description}</SheetDescription>
        </SheetHeader>
        {item && (
          <div className="flex flex-col gap-4 px-4 pb-6">
            <DetailRow label="ID" value={item.id} />
            {config.fields.map((field) => {
              const rawValue = getFieldValue(item, field.name);
              let value: React.ReactNode;
              if (field.type === "reference" && field.reference) {
                const map = referenceMaps[field.reference.resourceKey];
                const id = rawValue as number;
                value = map?.get(id) ?? id;
              } else if (field.type === "multi-reference" && field.reference) {
                const map = referenceMaps[field.reference.resourceKey];
                const ids = (rawValue as number[] | undefined) ?? [];
                value = ids.length
                  ? ids.map((id) => map?.get(id) ?? id).join(", ")
                  : "—";
              } else {
                value = formatValue(rawValue);
              }
              return <DetailRow key={field.name} label={field.label} value={value} />;
            })}
            <DetailRow
              label="Created"
              value={formatDate(getFieldValue(item, "created_at") as string | undefined)}
            />
            <DetailRow
              label="Last updated"
              value={formatDate(getFieldValue(item, "updated_at") as string | undefined)}
            />
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
