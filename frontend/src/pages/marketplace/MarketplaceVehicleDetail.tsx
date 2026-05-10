import { useQuery } from "@tanstack/react-query";
import {
  Award,
  Calendar,
  Car,
  CheckCircle2,
  Gauge,
  Heart,
  MapPin,
  MessageCircle,
  ShieldCheck,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { api } from "@/lib/api";
import type { Vehicle } from "@/types/api";

export function MarketplaceVehicleDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: vehicle, isLoading } = useQuery({
    queryKey: ["vehicle", id],
    queryFn: async (): Promise<Vehicle> => (await api.get(`/api/vehicles/${id}`)).data,
    enabled: Boolean(id),
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-[1400px] px-6 py-12">
        <div className="h-96 animate-pulse rounded-lg bg-slate-100" />
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="mx-auto max-w-[1400px] px-6 py-12 text-center">
        <p className="text-slate-500">Vehicle not found.</p>
        <Link to="/marketplace/catalog" className="mt-4 inline-block text-sm font-semibold underline">
          ← Back to Inventory
        </Link>
      </div>
    );
  }

  // CIF 가격 분해 — RoRo 평균 운임 + 1% 보험 (PoC 단순화, 실 환경은 destination 별 룩업)
  const fob = vehicle.list_price_usd ?? 0;
  const shipping = 1800; // Korea → 글로벌 RoRo 평균 ($1,500~$2,200 range)
  const insurance = Math.round(fob * 0.01);
  const cifBreakdown = { fob, shipping, insurance, total: fob + shipping + insurance };

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-6">
      {/* Breadcrumb */}
      <div className="mb-4 text-xs text-slate-500">
        <Link to="/marketplace" className="hover:text-slate-900">Home</Link>
        <span className="mx-2">›</span>
        <Link to="/marketplace/catalog" className="hover:text-slate-900">Used Car</Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900">{vehicle.make} {vehicle.model}</span>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_400px]">
        {/* Left — gallery + info */}
        <div>
          {/* Main image */}
          <div className="relative aspect-video overflow-hidden rounded-lg bg-gradient-to-br from-slate-100 to-slate-200">
            {vehicle.image_url ? (
              <img
                src={vehicle.image_url}
                alt={`${vehicle.make ?? ""} ${vehicle.model ?? ""} ${vehicle.year ?? ""}`.trim()}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center">
                <Car className="h-48 w-48 text-slate-300" />
              </div>
            )}
            <div className="absolute left-4 top-4 flex gap-2">
              <span className="rounded-md bg-amber-500 px-3 py-1 text-xs font-bold uppercase text-white">
                Inspected
              </span>
              {vehicle.steering && (
                <span className="rounded-md bg-slate-900 px-3 py-1 text-xs font-bold uppercase text-white">
                  {vehicle.steering}
                </span>
              )}
            </div>
            <button
              type="button"
              className="absolute right-4 top-4 rounded-full bg-white/90 p-2 backdrop-blur hover:bg-white"
              aria-label="Save"
            >
              <Heart className="h-5 w-5 text-slate-700" />
            </button>
          </div>

          {/* Thumbnail row — 같은 이미지 6번 (실제로는 angle 별 사진이지만 PoC) */}
          <div className="mt-3 flex gap-2 overflow-x-auto">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="flex h-20 w-28 shrink-0 cursor-pointer items-center justify-center overflow-hidden rounded border-2 border-transparent bg-slate-100 hover:border-slate-900"
              >
                {vehicle.image_url ? (
                  <img
                    src={vehicle.image_url}
                    alt=""
                    className="h-full w-full object-cover opacity-90 hover:opacity-100"
                  />
                ) : (
                  <Car className="h-8 w-8 text-slate-300" />
                )}
              </div>
            ))}
          </div>

          {/* Title + price */}
          <div className="mt-8">
            <h1 className="text-3xl font-bold leading-tight">
              {vehicle.make} {vehicle.model} {vehicle.year}
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              VIN: <span className="font-mono">{vehicle.vin ?? "—"}</span>
            </p>
          </div>

          {/* Spec table */}
          <div className="mt-6">
            <h2 className="text-base font-bold tracking-tight">Vehicle Specifications</h2>
            <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
              <Spec icon={Calendar} label="Year" value={vehicle.year ?? "—"} />
              <Spec icon={Gauge} label="Mileage" value={`${vehicle.mileage_km?.toLocaleString() ?? "—"} km`} />
              <Spec icon={Car} label="Engine" value={`${vehicle.engine_cc ?? "—"}cc`} />
              <Spec icon={Award} label="Fuel" value={vehicle.fuel_type ?? "—"} />
              <Spec icon={ShieldCheck} label="Transmission" value={vehicle.transmission ?? "—"} />
              <Spec icon={Award} label="Drivetrain" value={vehicle.drivetrain ?? "—"} />
              <Spec icon={Award} label="Color" value={vehicle.color_exterior ?? "—"} />
              <Spec icon={Award} label="Body" value={vehicle.body_type ?? "—"} />
              <Spec icon={Award} label="HS Code" value={vehicle.hs_code ?? "—"} />
            </div>
          </div>

          {/* Inspection report (Live Studio analog) */}
          <div className="mt-8 rounded-lg border bg-slate-50 p-6">
            <div className="mb-4 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <h2 className="text-base font-bold">112-Point Inspection Report</h2>
              <span className="ml-auto rounded-full bg-emerald-100 px-3 py-0.5 text-xs font-semibold text-emerald-800">
                Passed
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3">
              {[
                "Engine condition",
                "Transmission",
                "Brake system",
                "Suspension",
                "Electrical",
                "Body integrity",
              ].map((item) => (
                <div key={item} className="flex items-center gap-2 text-slate-700">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  {item}
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] text-slate-500">
              Full PDF report available upon request. Verified by certified Korean inspector.
            </p>
          </div>
        </div>

        {/* Right — sticky purchase panel with CIF breakdown */}
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-lg border bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-widest text-slate-500">Total CIF (worldwide)</p>
            <p className="mt-1 text-3xl font-bold text-slate-900">
              ${cifBreakdown.total.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              All-in to nearest port · Final CIF varies by destination
            </p>

            {/* Price breakdown */}
            <div className="mt-5 space-y-1.5 rounded-md bg-slate-50 p-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">Vehicle (FOB Incheon)</span>
                <span className="font-medium tabular-nums text-slate-900">
                  ${cifBreakdown.fob.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Ocean freight (RoRo est.)</span>
                <span className="font-medium tabular-nums text-slate-900">
                  ${cifBreakdown.shipping.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Marine insurance (~1%)</span>
                <span className="font-medium tabular-nums text-slate-900">
                  ${cifBreakdown.insurance.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between border-t border-slate-300 pt-1.5 text-sm font-bold text-slate-900">
                <span>CIF Total</span>
                <span className="tabular-nums">
                  ${cifBreakdown.total.toLocaleString()}
                </span>
              </div>
            </div>

            <button type="button" className="mt-5 w-full rounded-md bg-slate-900 py-3 text-sm font-semibold text-white hover:bg-slate-800">
              Request Quote
            </button>
            <button className="mt-2 flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              <MessageCircle className="h-4 w-4" /> Chat on WhatsApp
            </button>

            <div className="mt-6 space-y-3 border-t pt-4 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                Located in Incheon, Republic of Korea
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-3.5 w-3.5 text-slate-400" />
                Warranty Available · 30-day return policy
              </div>
              <div className="flex items-center gap-2">
                <Award className="h-3.5 w-3.5 text-slate-400" />
                Document service included (Invoice / B/L / C/O)
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900">
            <strong>Limited stock:</strong> This is a one-off vehicle. Reserve with deposit to
            secure.
          </div>
        </aside>
      </div>
    </div>
  );
}

function Spec({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Award;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
      <div>
        <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  );
}
