import { GapAnalysisPage } from "@/components/assessments/gap-analysis-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AssessmentGapsPage({ params }: PageProps) {
  const { id } = await params;
  return <GapAnalysisPage projectId={Number(id)} />;
}
