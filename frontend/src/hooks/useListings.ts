import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  ExportDocument,
  Listing,
  MailDraftResponse,
  Vehicle,
  Buyer,
  MailScenario,
} from "@/types/api";

// 쿼리 키 규칙 — 리소스 plural prefix 통일 (TanStack v5 prefix 매칭).
//   ["listings"]                       — 리스트/디테일 모두 invalidate
//   ["listings", "all" | <status>]     — 리스트
//   ["listings", "detail", <id>]       — 단건
// useBuyers / useVehicles 와 동일 패턴.

export function useListings(params?: { status?: string }) {
  return useQuery({
    queryKey: ["listings", params?.status ?? "all"],
    queryFn: async (): Promise<Listing[]> => {
      const r = await api.get<Listing[]>("/api/listings", {
        params: params?.status ? { status: params.status } : undefined,
      });
      return r.data;
    },
    staleTime: 30_000,
  });
}

export function useListing(id: string | undefined) {
  return useQuery({
    queryKey: ["listings", "detail", id],
    queryFn: async (): Promise<Listing> => {
      const r = await api.get<Listing>(`/api/listings/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });
}

export function useVehicle(id: string | undefined) {
  return useQuery({
    queryKey: ["vehicles", "detail", id],
    queryFn: async (): Promise<Vehicle> => {
      const r = await api.get<Vehicle>(`/api/vehicles/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });
}

export function useBuyerById(id: string | undefined) {
  return useQuery({
    queryKey: ["buyers", "detail", id],
    queryFn: async (): Promise<Buyer> => {
      const r = await api.get<Buyer>(`/api/buyers/${id}`);
      return r.data;
    },
    enabled: Boolean(id),
  });
}

export function useUpdateListingStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }): Promise<Listing> => {
      const r = await api.patch<Listing>(`/api/listings/${id}`, { status });
      return r.data;
    },
    // 옵티미스틱 업데이트 — rapid-click 시에도 UI 즉시 반영
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ["listings", "detail", id] });
      const prev = qc.getQueryData<Listing>(["listings", "detail", id]);
      if (prev) {
        qc.setQueryData<Listing>(["listings", "detail", id], { ...prev, status: status as Listing["status"] });
      }
      return { prev };
    },
    onError: (_e, { id }, ctx) => {
      if (ctx?.prev) qc.setQueryData(["listings", "detail", id], ctx.prev);
    },
    onSettled: (_d, _e, { id }) => {
      // 서버 truth 와 동기화
      qc.invalidateQueries({ queryKey: ["listings", "detail", id] });
      qc.invalidateQueries({ queryKey: ["listings"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

// ── 거래 생성 (마켓플레이스 'Request Quote' 흐름) ──────────
export interface CreateListingInput {
  vehicle_id: string;
  buyer_id: string;
  destination_country: string;
  notes?: string;
}

export function useCreateListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateListingInput): Promise<Listing> => {
      const r = await api.post<Listing>("/api/listings", input);
      return r.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["listings"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

// ── 메일 ──────────────────────────────────────────────────
export interface MailDraftInput {
  scenario: MailScenario;
  language?: string;
  extra_context?: string;
}

export function useMailDraft(listingId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: MailDraftInput): Promise<MailDraftResponse> => {
      if (!listingId) throw new Error("listingId required for mail-draft");
      const r = await api.post<MailDraftResponse>(
        `/api/listings/${listingId}/mail-draft`,
        input,
      );
      return r.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["listing-messages", listingId] });
    },
  });
}

// ── 서류 ──────────────────────────────────────────────────
export function useListingDocuments(listingId: string | undefined) {
  return useQuery({
    queryKey: ["listing-documents", listingId],
    queryFn: async (): Promise<ExportDocument[]> => {
      const r = await api.get<ExportDocument[]>(`/api/listings/${listingId}/documents`);
      return r.data;
    },
    enabled: Boolean(listingId),
  });
}

export function useGenerateDocuments(listingId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<{ documents: ExportDocument[] }> => {
      if (!listingId) throw new Error("listingId required for generate-documents");
      const r = await api.post<{ listing_id: string; documents: ExportDocument[] }>(
        `/api/listings/${listingId}/documents`,
      );
      return r.data;
    },
    // setQueryData 로 atomic swap — refetch flicker 방지
    onSuccess: (data) => {
      qc.setQueryData<ExportDocument[]>(
        ["listing-documents", listingId],
        data.documents,
      );
    },
  });
}
