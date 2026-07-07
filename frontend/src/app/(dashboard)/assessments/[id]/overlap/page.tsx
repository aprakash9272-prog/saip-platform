import { OverlapPage } from "@/components/assessments/overlap-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AssessmentOverlapPage({ params }: PageProps) {
  const { id } = await params;
  return <OverlapPage projectId={Number(id)} />;
}
