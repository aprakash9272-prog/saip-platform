import { RecommendationPage } from "@/components/assessments/recommendation-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AssessmentRecommendationsPage({ params }: PageProps) {
  const { id } = await params;
  return <RecommendationPage projectId={Number(id)} />;
}
