import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function OrganizationsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">
          Organizations
        </h2>
        <p className="text-sm text-muted-foreground">
          Manage the organizations onboarded to the platform.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>No organizations yet</CardTitle>
          <CardDescription>
            Organization management will be implemented in an upcoming
            sprint.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
