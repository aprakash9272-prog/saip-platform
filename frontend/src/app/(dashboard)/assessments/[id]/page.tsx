import { AssessmentProjectPage } from "@/components/assessments/assessment-project-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AssessmentPage({ params }: PageProps) {
  const { id } = await params;
  return <AssessmentProjectPage projectId={Number(id)} />;
}
