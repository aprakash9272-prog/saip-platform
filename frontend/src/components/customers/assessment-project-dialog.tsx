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
import { ASSESSMENT_STATUSES } from "@/lib/api/types";
import type { AssessmentProject } from "@/lib/api/types";

interface AssessmentProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  item?: AssessmentProject | null;
  onSubmit: (values: {
    name: string;
    status: string;
    start_date?: string | null;
    target_completion_date?: string | null;
    description?: string | null;
  }) => Promise<void>;
  submitting?: boolean;
  serverError?: string | null;
}

export function AssessmentProjectDialog({
  open,
  onOpenChange,
  mode,
  item,
  onSubmit,
  submitting,
  serverError,
}: AssessmentProjectDialogProps) {
  const [name, setName] = useState("");
  const [status, setStatus] = useState<string>(ASSESSMENT_STATUSES[0]);
  const [startDate, setStartDate] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName(item?.name ?? "");
      setStatus(item?.status ?? ASSESSMENT_STATUSES[0]);
      setStartDate(item?.start_date ?? "");
      setTargetDate(item?.target_completion_date ?? "");
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
      status,
      start_date: startDate || null,
      target_completion_date: targetDate || null,
      description: description.trim() || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "New Assessment Project" : "Edit Assessment Project"}
          </DialogTitle>
          <DialogDescription>
            A security assessment engagement for this customer.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ap-name">
              Name<span className="text-destructive"> *</span>
            </Label>
            <Input id="ap-name" value={name} onChange={(e) => setName(e.target.value)} />
            {nameError && <p className="text-sm text-destructive">{nameError}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ap-status">Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger id="ap-status" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ASSESSMENT_STATUSES.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ap-start">Start date</Label>
              <Input
                id="ap-start"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ap-target">Target completion</Label>
              <Input
                id="ap-target"
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ap-description">Description</Label>
            <Textarea
              id="ap-description"
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
