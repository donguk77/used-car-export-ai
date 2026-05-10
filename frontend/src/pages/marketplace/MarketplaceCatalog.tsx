import { useEffect, useMemo, useState } from "react";
import { Car, ChevronDown, Heart, MapPin, Search, X } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { useVehicles } from "@/hooks/useVehicles";
import { cn } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

// 한국 주요 모델 — body_type 보조 분류용. 모르면 passenger 는 Sedan 으로 fallback.
const SUV_MODELS = [
  "tucson", "santa fe", "palisade", "sportage", "sorento", "telluride",
  "kona", "stonic", "niro", "ev6", "ioniq 5", "ioniq 9", "creta", "venue",
  "mohave", "carnival",  // Carnival 은 minivan/SUV 경계
];
const SEDAN_MODELS = [
  "sonata", "avante", "elantra", "k5", "k3", "k7", "k8", "k9",
  "g70", "g80", "g90", "grandeur", "casper", "morning", "ray", "soul",
];

const CATEGORY_OPTIONS = ["All", "SUV/Crossover", "Sedan/Hatch", "Truck", "Van/MPV"];
const FUEL_OPTIONS = ["All", "Gasoline", "Diesel", "Hybrid", "EV"];
const BODY_OPTIONS = ["All", "passenger", "truck", "van"];
const YEAR_OPTIONS = ["All", "2022+", "2018-2021", "2014-2017", "Before 2014"];
const STEERING_OPTIONS = ["All", "LHD", "RHD"];

const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "price-asc", label: "Price: Low to High" },
  { value: "price-desc", label: "Price: High to Low" },
  { value: "mileage", label: "Mileage: Low to High" },
];

const PAGE_SIZE = 12;

interface FilterState {
  category: string;
  fuel: string;
  body: string;
  year: string;
  steering: string;
  search: string;
  sort: string;
}

const INITIAL_FILTERS: FilterState = {
  category: "All",
  fuel: "All",
  body: "All",
  year: "All",
  steering: "All",
  search: "",
  sort: "newest",
};

export function MarketplaceCatalog() {
  const { data: allVehicles, isLoading, isError } = useVehicles();
  const [searchParams] = useSearchParams();

  const [filters, setFilters] = useState<FilterState>({
    ...INITIAL_FILTERS,
    search: searchParams.get("q") ?? "",
  });
  const [page, setPage] = useState(1);

  // URL ?q= 가 외부 navigation 으로 변경되면 (예: landing hero search → /catalog?q=...)
  // search state 와 동기화. 같은 값이면 no-op (무한 루프 방지).
  useEffect(() => {
    const urlQ = searchParams.get("q") ?? "";
    setFilters((f) => (f.search === urlQ ? f : { ...f, search: urlQ }));
    setPage(1);
  }, [searchParams]);

  const set = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  const filtered = useMemo<Vehicle[]>(() => {
    if (!allVehicles) return [];
    let list = [...allVehicles];

    if (filters.category !== "All") list = list.filter((v) => matchCategory(v, filters.category));
    if (filters.fuel !== "All") list = list.filter((v) => v.fuel_type === filters.fuel);
    if (filters.body !== "All") list = list.filter((v) => v.body_type === filters.body);
    if (filters.year !== "All") list = list.filter((v) => matchYear(v.year, filters.year));
    if (filters.steering !== "All") list = list.filter((v) => v.steering === filters.steering);

    if (filters.search.trim()) {
      const q = filters.search.toLowerCase();
      list = list.filter((v) =>
        [v.vin, v.make, v.model, String(v.year), v.color_exterior]
          .filter(Boolean)
          .some((field) => field!.toLowerCase().includes(q)),
      );
    }

    if (filters.sort === "price-asc") list.sort((a, b) => (a.list_price_usd ?? 0) - (b.list_price_usd ?? 0));
    else if (filters.sort === "price-desc") list.sort((a, b) => (b.list_price_usd ?? 0) - (a.list_price_usd ?? 0));
    else if (filters.sort === "mileage") list.sort((a, b) => (a.mileage_km ?? 0) - (b.mileage_km ?? 0));

    return list;
  }, [allVehicles, filters]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageStart = (page - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(pageStart, pageStart + PAGE_SIZE);

  const activeFilterCount =
    Object.entries(filters).filter(([k, v]) => k !== "sort" && k !== "search" && v !== "All").length +
    (filters.search.trim() ? 1 : 0);

  const clearAll = () => {
    setFilters(INITIAL_FILTERS);
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-8">
      <div className="mb-4 text-xs text-slate-500">
        <Link to="/marketplace" className="hover:text-slate-900">Home</Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900">Used Car Inventory</span>
      </div>

      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Used Car Inventory</h1>
          <p className="mt-1 text-sm text-slate-500">
            {filtered.length} of {allVehicles?.length ?? 0} vehicles · Updated daily from Korean auctions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Sort by:</span>
          <select
            value={filters.sort}
            onChange={(e) => set("sort", e.target.value)}
            className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm focus:border-slate-900 focus:outline-none"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border bg-slate-50 px-4 py-3">
        <div className="relative min-w-[240px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search by VIN, make, model, year, or color..."
            value={filters.search}
            onChange={(e) => set("search", e.target.value)}
            className="h-9 w-full rounded-md border border-slate-300 bg-white pl-9 pr-3 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
          />
        </div>
        {activeFilterCount > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            <X className="h-3 w-3" /> Clear filters ({activeFilterCount})
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
        <aside className="space-y-6">
          <FilterGroup title="Category" options={CATEGORY_OPTIONS} value={filters.category} onChange={(v) => set("category", v)} />
          <FilterGroup title="Fuel Type" options={FUEL_OPTIONS} value={filters.fuel} onChange={(v) => set("fuel", v)} />
          <FilterGroup
            title="Body Style"
            options={BODY_OPTIONS}
            labels={{ passenger: "Passenger", truck: "Truck", van: "Van" }}
            value={filters.body}
            onChange={(v) => set("body", v)}
          />
          <FilterGroup title="Year Range" options={YEAR_OPTIONS} value={filters.year} onChange={(v) => set("year", v)} />
          <FilterGroup title="Steering" options={STEERING_OPTIONS} value={filters.steering} onChange={(v) => set("steering", v)} />
        </aside>

        <div className="space-y-6">
          {isLoading && (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
            </div>
          )}

          {isError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-900">
              Failed to load vehicles. Please refresh or try again later.
            </div>
          )}

          {!isLoading && !isError && filtered.length === 0 && (
            <div className="rounded-lg border border-dashed bg-slate-50 py-16 text-center">
              <Car className="mx-auto h-12 w-12 text-slate-300" />
              <p className="mt-3 text-sm font-medium text-slate-700">No vehicles match your filters</p>
              <p className="mt-1 text-xs text-slate-500">Try adjusting your filters above</p>
              {activeFilterCount > 0 && (
                <button
                  type="button"
                  onClick={clearAll}
                  className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800"
                >
                  Clear all filters
                </button>
              )}
            </div>
          )}

          {!isLoading && !isError && pageItems.length > 0 && (
            <>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {pageItems.map((v) => <MarketplaceCard key={v.id} vehicle={v} />)}
              </div>
              {totalPages > 1 && <Pagination page={page} totalPages={totalPages} onChange={setPage} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function matchCategory(v: Vehicle, category: string): boolean {
  const m = (v.model ?? "").toLowerCase();
  if (category === "Truck") return v.body_type === "truck";
  if (category === "Van/MPV") return v.body_type === "van" || /starex|staria|carnival/i.test(m);

  const isSuv = SUV_MODELS.some((k) => m.includes(k));
  const isSedan = SEDAN_MODELS.some((k) => m.includes(k));
  const isPassenger = v.body_type === "passenger";

  if (category === "SUV/Crossover") return isSuv;
  // 모르는 passenger 모델은 일단 Sedan/Hatch 로 (가장 흔한 분류)
  if (category === "Sedan/Hatch") return isSedan || (isPassenger && !isSuv);
  return true;
}

function matchYear(year: number | null, range: string): boolean {
  if (year === null) return false;
  if (range === "2022+") return year >= 2022;
  if (range === "2018-2021") return year >= 2018 && year <= 2021;
  if (range === "2014-2017") return year >= 2014 && year <= 2017;
  if (range === "Before 2014") return year < 2014;
  return true;
}

function FilterGroup({
  title,
  options,
  labels,
  value,
  onChange,
}: {
  title: string;
  options: string[];
  labels?: Record<string, string>;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-700">{title}</h3>
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </div>
      <div className="space-y-1.5">
        {options.map((opt) => (
          <label
            key={opt}
            className={cn(
              "flex cursor-pointer items-center gap-2 text-sm transition",
              value === opt ? "font-semibold text-slate-900" : "text-slate-600 hover:text-slate-900",
            )}
          >
            <input
              type="radio"
              name={title}
              checked={value === opt}
              onChange={() => onChange(opt)}
              className="h-3.5 w-3.5 accent-slate-900"
            />
            {labels?.[opt] ?? opt}
          </label>
        ))}
      </div>
    </div>
  );
}

function MarketplaceCard({ vehicle }: { vehicle: Vehicle }) {
  return (
    <Link
      to={`/marketplace/${vehicle.id}`}
      className="group flex flex-col overflow-hidden rounded-lg border bg-white shadow-sm transition hover:shadow-lg"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200">
        {vehicle.image_url ? (
          <img
            src={vehicle.image_url}
            alt={`${vehicle.make ?? ""} ${vehicle.model ?? ""} ${vehicle.year ?? ""}`.trim()}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <Car className="h-20 w-20 text-slate-400 transition group-hover:scale-110" />
          </div>
        )}
        <button
          type="button"
          onClick={(e) => { e.preventDefault(); }}
          className="absolute right-3 top-3 rounded-full bg-white/90 p-1.5 text-slate-600 backdrop-blur transition hover:bg-white hover:text-rose-500"
          aria-label="Save to favorites"
        >
          <Heart className="h-4 w-4" />
        </button>
        {vehicle.steering && (
          <span className="absolute left-3 top-3 rounded bg-slate-900/80 px-2 py-0.5 text-[10px] font-bold uppercase text-white backdrop-blur">
            {vehicle.steering}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <p className="truncate text-sm font-bold leading-tight">
          {vehicle.make} {vehicle.model}
        </p>
        <p className="mt-0.5 text-xs text-slate-500">
          {vehicle.year} · {vehicle.engine_cc}cc · {vehicle.fuel_type}
        </p>
        <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500">
          <span>{vehicle.mileage_km?.toLocaleString()} km</span>
          {vehicle.color_exterior && (<><span>·</span><span>{vehicle.color_exterior}</span></>)}
        </div>
        <div className="mt-auto flex items-center justify-between border-t pt-3">
          <span className="text-lg font-bold text-slate-900">
            ${vehicle.list_price_usd?.toLocaleString()}
          </span>
          <span className="flex items-center gap-1 text-[10px] text-slate-500">
            <MapPin className="h-3 w-3" /> Incheon, KR
          </span>
        </div>
      </div>
    </Link>
  );
}

function CardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border bg-white">
      <div className="aspect-[4/3] animate-pulse bg-slate-100" />
      <div className="space-y-2 p-4">
        <div className="h-4 w-3/4 animate-pulse rounded bg-slate-100" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
        <div className="h-3 w-1/3 animate-pulse rounded bg-slate-100" />
        <div className="flex justify-between border-t pt-3">
          <div className="h-5 w-16 animate-pulse rounded bg-slate-100" />
          <div className="h-3 w-12 animate-pulse rounded bg-slate-100" />
        </div>
      </div>
    </div>
  );
}

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  const windowSize = 5;
  const start = Math.max(1, Math.min(totalPages - windowSize + 1, page - Math.floor(windowSize / 2)));
  const end = Math.min(totalPages, start + windowSize - 1);
  const numbers = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  return (
    <div className="flex items-center justify-center gap-1 pt-2">
      <button
        type="button"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        ‹ Prev
      </button>
      {start > 1 && (
        <>
          <PageBtn page={1} active={false} onChange={onChange} />
          <span className="px-1 text-xs text-slate-400">…</span>
        </>
      )}
      {numbers.map((n) => <PageBtn key={n} page={n} active={n === page} onChange={onChange} />)}
      {end < totalPages && (
        <>
          <span className="px-1 text-xs text-slate-400">…</span>
          <PageBtn page={totalPages} active={false} onChange={onChange} />
        </>
      )}
      <button
        type="button"
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Next ›
      </button>
    </div>
  );
}

function PageBtn({
  page,
  active,
  onChange,
}: {
  page: number;
  active: boolean;
  onChange: (p: number) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(page)}
      className={cn(
        "min-w-[32px] rounded-md px-2 py-1.5 text-xs font-medium transition",
        active ? "bg-slate-900 text-white" : "border border-slate-300 text-slate-700 hover:bg-slate-50",
      )}
    >
      {page}
    </button>
  );
}
