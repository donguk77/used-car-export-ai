import { useState } from "react";
import { ArrowRight, Award, Car, Gavel, Globe, Search, ShieldCheck } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useVehicles } from "@/hooks/useVehicles";
import { cn } from "@/lib/utils";

const KEYWORD_CHIPS = [
  "AutoExport Stock",
  "Warranty Available",
  "SUV+Diesel",
  "4WD",
  "Manual",
  "Sunroof",
  "Smart Key",
  "Over 6-Seater",
];

export function MarketplaceLanding() {
  const { data: vehicles } = useVehicles();
  const featured = vehicles?.slice(0, 4) ?? [];
  const [heroSearch, setHeroSearch] = useState("");
  const navigate = useNavigate();

  const submitSearch = () => {
    // catalog 페이지로 검색어와 함께 이동 — 폴리시: URL 쿼리로 hand-off (Phase 2)
    navigate(`/marketplace/catalog${heroSearch.trim() ? `?q=${encodeURIComponent(heroSearch.trim())}` : ""}`);
  };

  return (
    <div>
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-8 px-6 py-16 lg:grid-cols-2 lg:py-24">
          <div className="flex flex-col justify-center">
            <span className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wider">
              <Award className="h-3 w-3" /> Korea's Trusted Used Car Marketplace
            </span>
            <h1 className="text-4xl font-bold leading-tight tracking-tight lg:text-5xl">
              Korean Used Cars,
              <br />
              Inspected &amp; Globally Shipped
            </h1>
            <p className="mt-4 max-w-md text-base text-slate-300">
              Browse {vehicles?.length ?? 0}+ verified vehicles. Direct from Hyundai, Kia, Genesis,
              KGM. Door-to-door shipping with warranty.
            </p>
            {/* Hero search bar (Autobell-style) */}
            <form
              onSubmit={(e) => { e.preventDefault(); submitSearch(); }}
              className="mt-8 flex w-full max-w-md overflow-hidden rounded-md bg-white shadow-lg"
            >
              <div className="flex flex-1 items-center gap-2 px-4">
                <Search className="h-4 w-4 text-slate-400" />
                <input
                  type="search"
                  placeholder="Search Hyundai Sonata, Kia Sorento, VIN..."
                  value={heroSearch}
                  onChange={(e) => setHeroSearch(e.target.value)}
                  className="h-12 w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
                />
              </div>
              <button
                type="submit"
                className="bg-slate-900 px-6 text-sm font-semibold text-white hover:bg-slate-800"
              >
                Search
              </button>
            </form>

            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                to="/marketplace/catalog"
                className="inline-flex items-center gap-2 rounded-md bg-white/10 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/20 transition hover:bg-white/20"
              >
                Browse Inventory <ArrowRight className="h-4 w-4" />
              </Link>
              <button className="inline-flex items-center gap-2 rounded-md px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">
                <Gavel className="h-4 w-4" /> Next Auction
              </button>
            </div>

            {/* Trust marks + live vehicle count badge */}
            <div className="mt-10 flex flex-wrap gap-6 text-xs text-slate-400">
              <a href="/marketplace/catalog" className="flex items-center gap-1.5 underline-offset-4 hover:text-white hover:underline">
                <ShieldCheck className="h-3.5 w-3.5" />
                <strong className="text-white">{(vehicles?.length ?? 0).toLocaleString()}+</strong> Vehicles Available
              </a>
              <div className="flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5" /> 100+ Countries Shipped
              </div>
              <div className="flex items-center gap-1.5">
                <Award className="h-3.5 w-3.5" /> Warranty Available
              </div>
            </div>
          </div>

          {/* Featured vehicle preview */}
          <div className="relative">
            {featured[0] ? (
              <Link
                to={`/marketplace/${featured[0].id}`}
                className="block overflow-hidden rounded-lg bg-white text-slate-900 shadow-2xl transition hover:scale-[1.02]"
              >
                <div className="relative aspect-[16/10] overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200">
                  {featured[0].image_url ? (
                    <img
                      src={featured[0].image_url}
                      alt={`${featured[0].make ?? ""} ${featured[0].model ?? ""}`.trim()}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <Car className="h-32 w-32 text-slate-300" />
                    </div>
                  )}
                  <div className="absolute left-4 top-4 rounded-md bg-amber-500 px-3 py-1 text-xs font-bold uppercase tracking-wider text-white">
                    Featured
                  </div>
                </div>
                <div className="p-6">
                  <p className="text-xl font-bold">
                    {featured[0].make} {featured[0].model} {featured[0].year}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    {featured[0].engine_cc}cc · {featured[0].fuel_type} · {featured[0].mileage_km?.toLocaleString()} km
                  </p>
                  <div className="mt-4 flex items-baseline justify-between">
                    <span className="text-2xl font-bold text-slate-900">
                      ${featured[0].list_price_usd?.toLocaleString()}
                    </span>
                    <span className="text-xs text-slate-500">
                      CIF available · Worldwide shipping
                    </span>
                  </div>
                </div>
              </Link>
            ) : (
              <div className="flex aspect-[16/10] items-center justify-center rounded-lg border border-white/20 bg-white/5">
                <Car className="h-24 w-24 text-white/20" />
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Keyword chips (Autobell-style suggestion bar) */}
      <section className="border-b bg-slate-50">
        <div className="mx-auto max-w-[1400px] px-6 py-6">
          <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Popular Keywords
          </div>
          <div className="flex flex-wrap gap-2">
            {KEYWORD_CHIPS.map((kw, i) => (
              <Link
                key={kw}
                to="/marketplace/catalog"
                className={cn(
                  "rounded-full border px-4 py-1.5 text-xs font-medium transition",
                  i === 0
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-300 bg-white text-slate-600 hover:border-slate-900 hover:text-slate-900",
                )}
              >
                {kw}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured cars carousel */}
      <section className="mx-auto max-w-[1400px] px-6 py-12">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Special used cars only at AutoExport</h2>
            <p className="mt-1 text-sm text-slate-500">
              Hand-picked by our 112-point inspection team
            </p>
          </div>
          <Link
            to="/marketplace/catalog"
            className="text-sm font-semibold text-slate-900 hover:underline"
          >
            View All →
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {featured.map((v) => (
            <Link
              key={v.id}
              to={`/marketplace/${v.id}`}
              className="group block overflow-hidden rounded-lg border bg-white shadow-sm transition hover:shadow-lg"
            >
              <div className="aspect-video overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200 transition group-hover:from-slate-200 group-hover:to-slate-300">
                {v.image_url ? (
                  <img
                    src={v.image_url}
                    alt={`${v.make ?? ""} ${v.model ?? ""}`.trim()}
                    className="h-full w-full object-cover transition-transform group-hover:scale-105"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <Car className="h-16 w-16 text-slate-400" />
                  </div>
                )}
              </div>
              <div className="p-4">
                <p className="truncate text-sm font-bold">
                  {v.make} {v.model} {v.year}
                </p>
                <p className="mt-1 truncate text-xs text-slate-500">
                  {v.engine_cc}cc · {v.fuel_type} · {v.mileage_km?.toLocaleString()} km
                </p>
                <p className="mt-3 text-lg font-bold text-slate-900">
                  ${v.list_price_usd?.toLocaleString()}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* About — stats cards (trust signal, Autobell-style) */}
      <section className="bg-slate-50 border-y">
        <div className="mx-auto max-w-[1400px] px-6 py-16">
          <div className="mb-10 text-center">
            <p className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-500">
              About AutoExport Global
            </p>
            <h2 className="text-3xl font-bold tracking-tight">The AI-First Korean Used-Car Export Platform</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-600">
              Built for SME exporters in Songdo, Incheon. AI-powered import-rule
              checks, multilingual buyer correspondence, and auto-generated export
              documents — all in one workflow.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            <StatCard value={(vehicles?.length ?? 0).toString()} label="Vehicles in stock" hint="Updated daily" />
            <StatCard value="5" label="Destination countries" hint="DO · KE · LY · KG · SY" />
            <StatCard value="5" label="Languages supported" hint="EN · ES · AR · RU · KR" />
            <StatCard value="4" label="Auto-generated docs" hint="Invoice · PL · SI · C/O" />
          </div>
        </div>
      </section>

      {/* Auction promo */}
      <section className="bg-slate-900 text-white">
        <div className="mx-auto flex max-w-[1400px] flex-col items-center gap-6 px-6 py-12 sm:flex-row sm:justify-between">
          <div>
            <span className="mb-2 inline-block rounded-md bg-amber-500/20 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-amber-300">
              Weekly Auction
            </span>
            <h2 className="text-2xl font-bold tracking-tight">Korea's No.1 Used Car Auction</h2>
            <p className="mt-2 text-sm text-slate-300">
              Live bidding every Wednesday · Reserve your seat with one click.
            </p>
          </div>
          <button type="button" className="inline-flex items-center gap-2 rounded-md bg-white px-6 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-100">
            <Gavel className="h-4 w-4" /> Check the next Auction
          </button>
        </div>
      </section>
    </div>
  );
}

function StatCard({ value, label, hint }: { value: string; label: string; hint: string }) {
  return (
    <div className="text-center">
      <p className="text-4xl font-extrabold tracking-tight text-slate-900 tabular-nums sm:text-5xl">
        {value}
        <span className="text-2xl font-bold text-amber-500">+</span>
      </p>
      <p className="mt-2 text-sm font-semibold text-slate-700">{label}</p>
      <p className="mt-0.5 text-[11px] text-slate-500">{hint}</p>
    </div>
  );
}
