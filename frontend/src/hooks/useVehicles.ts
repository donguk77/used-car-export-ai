import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Vehicle } from "@/types/api";

export function useVehicles(params?: { status?: string }) {
  return useQuery({
    queryKey: ["vehicles", params?.status ?? "all"],
    queryFn: async (): Promise<Vehicle[]> => {
      const r = await api.get<Vehicle[]>("/api/vehicles", {
        params: params?.status ? { status: params.status } : undefined,
      });
      return r.data;
    },
    staleTime: 30_000,
  });
}
