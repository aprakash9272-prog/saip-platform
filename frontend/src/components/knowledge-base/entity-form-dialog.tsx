"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import type { Resolver } from "react-hook-form";
import { Controller, useForm } from "react-hook-form";
import type { ZodTypeAny } from "zod";

// Every entity has its own concrete zod schema (see resource-configs.ts), but
// the form dialog is generic over all of them, so the resolver is built from
// a config-supplied ZodTypeAny rather than one fixed schema type.
const buildResolver = zodResolver as unknown as (
  schema: ZodTypeAny,
) => Resolver<Record<string, unknown>>;

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

import { RESOURCE_REGISTRY } from "./resource-configs";
import type { FieldConfig, ResourceConfig } from "./types";
import { getFieldValue } from "./types";

interface EntityFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: ResourceConfig;
  mode: "create" | "edit";
  defaultValues?: Record<string, unknown>;
  onSubmit: (values: Record<string, unknown>) => Promise<void>;
  submitting?: boolean;
  serverError?: string | null;
}

function singular(title: string): string {
  return title.endsWith("s") ? title.slice(0, -1) : title;
}

function ReferenceSelectField({
  field,
  value,
  onChange,
}: {
  field: FieldConfig;
  value: unknown;
  onChange: (value: string) => void;
}) {
  const refConfig = field.reference!;
  const refApi = RESOURCE_REGISTRY[refConfig.resourceKey].api;
  const { data, isLoading } = useResourceOptions(refConfig.resourceKey, refApi);
  const currentValue =
    value !== undefined && value !== null && value !== "" ? String(value) : "";

  return (
    <Select value={currentValue} onValueChange={onChange}>
      <SelectTrigger id={field.name} className="w-full">
        <SelectValue
          placeholder={isLoading ? "Loading..." : `Select ${field.label.toLowerCase()}`}
        />
      </SelectTrigger>
      <SelectContent>
        {(data?.items ?? []).map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {String(getFieldValue(item, refConfig.labelField))}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function MultiReferenceField({
  field,
  value,
  onChange,
}: {
  field: FieldConfig;
  value: unknown;
  onChange: (value: number[]) => void;
}) {
  const refConfig = field.reference!;
  const refApi = RESOURCE_REGISTRY[refConfig.resourceKey].api;
  const { data, isLoading } = useResourceOptions(refConfig.resourceKey, refApi);
  const selected = new Set((Array.isArray(value) ? value : []).map(Number));

  const toggle = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(Array.from(next));
  };

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading options...</p>;
  }

  const options = data?.items ?? [];

  return (
    <div className="flex max-h-40 flex-col gap-1 overflow-y-auto rounded-md border p-2">
      {options.length === 0 && (
        <p className="text-sm text-muted-foreground">No options available.</p>
      )}
      {options.map((item) => (
        <label key={item.id} className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={selected.has(item.id)}
            onChange={() => toggle(item.id)}
            className="size-4 rounded border-input"
          />
          {String(getFieldValue(item, refConfig.labelField))}
        </label>
      ))}
    </div>
  );
}

function FixedSelectField({
  field,
  value,
  onChange,
}: {
  field: FieldConfig;
  value: unknown;
  onChange: (value: string) => void;
}) {
  const currentValue = value !== undefined && value !== null ? String(value) : "";

  return (
    <Select value={currentValue} onValueChange={onChange}>
      <SelectTrigger id={field.name} className="w-full">
        <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
      </SelectTrigger>
      <SelectContent>
        {(field.options ?? []).map((option) => (
          <SelectItem key={option} value={option}>
            {option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function FixedMultiSelectField({
  field,
  value,
  onChange,
}: {
  field: FieldConfig;
  value: unknown;
  onChange: (value: string[]) => void;
}) {
  const selected = new Set(Array.isArray(value) ? (value as string[]) : []);

  const toggle = (option: string) => {
    const next = new Set(selected);
    if (next.has(option)) next.delete(option);
    else next.add(option);
    onChange(Array.from(next));
  };

  return (
    <div className="flex flex-wrap gap-3 rounded-md border p-2">
      {(field.options ?? []).map((option) => (
        <label key={option} className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={selected.has(option)}
            onChange={() => toggle(option)}
            className="size-4 rounded border-input"
          />
          {option}
        </label>
      ))}
    </div>
  );
}

function BooleanField({
  value,
  onChange,
  label,
}: {
  value: unknown;
  onChange: (value: boolean) => void;
  label: string;
}) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(event) => onChange(event.target.checked)}
        className="size-4 rounded border-input"
      />
      {label}
    </label>
  );
}

export function EntityFormDialog({
  open,
  onOpenChange,
  config,
  mode,
  defaultValues,
  onSubmit,
  submitting,
  serverError,
}: EntityFormDialogProps) {
  const schema = mode === "create" ? config.createSchema : config.updateSchema;
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Record<string, unknown>>({
    resolver: buildResolver(schema),
    defaultValues: defaultValues ?? {},
  });

  useEffect(() => {
    if (open) reset(defaultValues ?? {});
  }, [open, defaultValues, reset]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(values);
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? `New ${singular(config.title)}` : `Edit ${singular(config.title)}`}
          </DialogTitle>
          <DialogDescription>{config.description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="flex flex-col gap-4">
          {config.fields.map((field) => (
            <div key={field.name} className="flex flex-col gap-1.5">
              {field.type !== "boolean" && (
                <Label htmlFor={field.name}>
                  {field.label}
                  {field.required && <span className="text-destructive"> *</span>}
                </Label>
              )}
              <Controller
                control={control}
                name={field.name}
                render={({ field: rhfField }) => {
                  if (field.type === "boolean") {
                    return (
                      <BooleanField
                        value={rhfField.value}
                        onChange={rhfField.onChange}
                        label={field.label}
                      />
                    );
                  }
                  if (field.type === "textarea") {
                    return (
                      <Textarea
                        id={field.name}
                        placeholder={field.placeholder}
                        value={(rhfField.value as string) ?? ""}
                        onChange={rhfField.onChange}
                      />
                    );
                  }
                  if (field.type === "reference") {
                    return (
                      <ReferenceSelectField
                        field={field}
                        value={rhfField.value}
                        onChange={rhfField.onChange}
                      />
                    );
                  }
                  if (field.type === "multi-reference") {
                    return (
                      <MultiReferenceField
                        field={field}
                        value={rhfField.value}
                        onChange={rhfField.onChange}
                      />
                    );
                  }
                  if (field.type === "select") {
                    return (
                      <FixedSelectField
                        field={field}
                        value={rhfField.value}
                        onChange={rhfField.onChange}
                      />
                    );
                  }
                  if (field.type === "multi-select") {
                    return (
                      <FixedMultiSelectField
                        field={field}
                        value={rhfField.value}
                        onChange={rhfField.onChange}
                      />
                    );
                  }
                  return (
                    <Input
                      id={field.name}
                      placeholder={field.placeholder}
                      value={(rhfField.value as string) ?? ""}
                      onChange={rhfField.onChange}
                    />
                  );
                }}
              />
              {errors[field.name] && (
                <p className="text-sm text-destructive">
                  {String(errors[field.name]?.message)}
                </p>
              )}
            </div>
          ))}
          {serverError && <p className="text-sm text-destructive">{serverError}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : mode === "create" ? "Create" : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
