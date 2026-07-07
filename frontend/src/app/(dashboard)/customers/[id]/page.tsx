import { CustomerDetailPage } from "@/components/customers/customer-detail-page";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CustomerPage({ params }: PageProps) {
  const { id } = await params;
  return <CustomerDetailPage customerId={Number(id)} />;
}
