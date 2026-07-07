import { SimulationPage } from "@/components/assessments/simulation-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AssessmentSimulationPage({ params }: PageProps) {
  const { id } = await params;
  return <SimulationPage projectId={Number(id)} />;
}
