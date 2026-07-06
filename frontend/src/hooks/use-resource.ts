import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ListParams, ResourceApi } from "@/lib/api/resources";

export function useResourceQueries<TRead, TCreate, TUpdate>(
  key: string,
  api: ResourceApi<TRead, TCreate, TUpdate>,
  params: ListParams,
) {
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: [key, "list", params],
    queryFn: () => api.list(params),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: [key, "list"] });

  const createMutation = useMutation({
    mutationFn: (payload: TCreate) => api.create(payload),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: TUpdate }) =>
      api.update(id, payload),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.remove(id),
    onSuccess: invalidate,
  });

  return { listQuery, createMutation, updateMutation, deleteMutation };
}

export function useResourceOptions<TRead>(
  key: string,
  api: ResourceApi<TRead, unknown, unknown>,
) {
  return useQuery({
    queryKey: [key, "options"],
    queryFn: () => api.list({ limit: 200 }),
  });
}
