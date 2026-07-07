"use client";

import { useEffect, useState } from "react";

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
import { ENVIRONMENT_TYPES } from "@/lib/api/types";
import type { Environment } from "@/lib/api/types";

interface EnvironmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  item?: Environment | null;
  onSubmit: (values: {
    name: string;
    environment_type: string;
    description?: string | null;
  }) => Promise<void>;
  submitting?: boolean;
  serverError?: string | null;
}

export function EnvironmentDialog({
  open,
  onOpenChange,
  mode,
  item,
  onSubmit,
  submitting,
  serverError,
}: EnvironmentDialogProps) {
  const [name, setName] = useState("");
  const [environmentType, setEnvironmentType] = useState<string>(ENVIRONMENT_TYPES[0]);
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(item?.name ?? "");
      setEnvironmentType(item?.environment_type ?? ENVIRONMENT_TYPES[0]);
      setDescription(item?.description ?? "");
      setNameError(null);
    }
  }, [open, item]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) {
      setNameError("Name is required");
      return;
    }
    await onSubmit({
      name: name.trim(),
      environment_type: environmentType,
      description: description.trim() || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "New Environment" : "Edit Environment"}</DialogTitle>
          <DialogDescription>
            A deployment tier within this customer&apos;s infrastructure.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="env-name">
              Name<span className="text-destructive"> *</span>
            </Label>
            <Input id="env-name" value={name} onChange={(e) => setName(e.target.value)} />
            {nameError && <p className="text-sm text-destructive">{nameError}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="env-type">
              Type<span className="text-destructive"> *</span>
            </Label>
            <Select value={environmentType} onValueChange={setEnvironmentType}>
              <SelectTrigger id="env-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ENVIRONMENT_TYPES.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="env-description">Description</Label>
            <Textarea
              id="env-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
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
