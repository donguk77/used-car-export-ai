import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Buyer, BuyerCreateResponse, ComplianceReport } from "@/types/api";

export function useBuyers(params?: { sanctions_status?: string }) {
  return useQuery({
    queryKey: ["buyers", params?.sanctions_status ?? "all"],
    queryFn: async (): Promise<Buyer[]> => {
      const r = await api.get<Buyer[]>("/api/buyers", {
        params: params?.sanctions_status
          ? { sanctions_status: params.sanctions_status }
          : undefined,
      });
      return r.data;
    },
    staleTime: 30_000,
  });
}

// 모든 mutation 은 ["buyers"] prefix 로 invalidate → 모든 필터 변형
// (["buyers", "all"], ["buyers", "clean"], ...) 가 동시 갱신됨.
// TanStack v5 partial-key 매칭으로 의도된 동작.

// useListings.ts:useBuyerById 와 같은 캐시 키 ("buyers" prefix) 사용 — 한쪽에서
// invalidate 하면 양쪽 화면이 함께 갱신되도록.
export function useBuyer(id: string | undefined) {
  return useQuery({
    queryKey: ["buyers", "detail", id],
    queryFn: async (): Promise<Buyer> => {
      const r = await api.get<Buyer>(`/api/buyers/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });
}

export type CreateBuyerInput = Partial<Omit<Buyer, "id" | "sanctions_status" | "russia_proxy_risk_score" | "total_orders">> & {
  country_code: string;
};

export function useCreateBuyer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateBuyerInput): Promise<BuyerCreateResponse> => {
      const r = await api.post<BuyerCreateResponse>("/api/buyers", data);
      return r.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buyers"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

export function useRecheckBuyer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<ComplianceReport> => {
      const r = await api.post<ComplianceReport>(`/api/buyers/${id}/recheck`);
      return r.data;
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["buyer", id] });
      qc.invalidateQueries({ queryKey: ["buyers"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

export function useDeleteBuyer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/buyers/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buyers"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}
