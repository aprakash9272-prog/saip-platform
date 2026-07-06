import { Building2, LayoutDashboard, ShieldCheck } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const SUMMARY_CARDS = [
  {
    title: "Organizations",
    description: "Onboarded organizations",
    icon: Building2,
  },
  {
    title: "Capabilities",
    description: "Tracked security capabilities",
    icon: ShieldCheck,
  },
  {
    title: "Assessments",
    description: "Completed maturity assessments",
    icon: LayoutDashboard,
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">
          Welcome to SAIP
        </h2>
        <p className="text-sm text-muted-foreground">
          Security Architecture Intelligence Platform &mdash; foundation
          workspace. Business modules will appear here as they ship.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SUMMARY_CARDS.map((card) => (
          <Card key={card.title}>
            <CardHeader>
              <card.icon className="size-5 text-muted-foreground" />
              <CardTitle>{card.title}</CardTitle>
              <CardDescription>{card.description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
