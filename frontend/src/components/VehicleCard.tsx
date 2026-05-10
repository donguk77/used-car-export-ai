import { Car, Gauge } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { FUEL_LABEL, VEHICLE_STATUS_LABEL, VEHICLE_STATUS_VARIANT } from "@/lib/constants";
import { formatPrice } from "@/lib/utils";
import type { Vehicle } from "@/types/api";

export function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  const label = `${vehicle.make ?? "?"} ${vehicle.model ?? "?"} ${vehicle.year ?? ""}`.trim();
  const fuel = FUEL_LABEL[vehicle.fuel_type ?? ""] ?? vehicle.fuel_type ?? "—";
  const cc = vehicle.engine_cc ? `${(vehicle.engine_cc / 1000).toFixed(1)}L` : null;
  const statusVariant = VEHICLE_STATUS_VARIANT[vehicle.status] ?? "outline";

  return (
    <Link
      to={`/vehicles/${vehicle.id}`}
      className="group flex flex-col overflow-hidden rounded-lg border bg-card shadow-sm transition-all hover:border-primary/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-muted to-muted/40">
        {vehicle.image_url ? (
          <img
            src={vehicle.image_url}
            alt={`${vehicle.make ?? ""} ${vehicle.model ?? ""} ${vehicle.year ?? ""}`.trim()}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center opacity-30 transition-opacity group-hover:opacity-50">
            <Car className="h-16 w-16 text-muted-foreground" />
          </div>
        )}
        <div className="absolute right-2 top-2">
          <Badge variant={statusVariant}>
            {VEHICLE_STATUS_LABEL[vehicle.status] ?? vehicle.status}
          </Badge>
        </div>
        {vehicle.steering && (
          <div className="absolute left-2 top-2">
            <Badge variant="outline" className="bg-background/80 backdrop-blur">
              {vehicle.steering}
            </Badge>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div>
          <p className="truncate font-semibold leading-tight">{label}</p>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {[cc, fuel, vehicle.body_type].filter(Boolean).join(" · ") || "—"}
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {vehicle.mileage_km !== null && vehicle.mileage_km !== undefined && (
            <span className="flex items-center gap-1">
              <Gauge className="h-3 w-3" />
              {vehicle.mileage_km.toLocaleString()} km
            </span>
          )}
          {vehicle.color_exterior && <span className="truncate">{vehicle.color_exterior}</span>}
        </div>

        <div className="mt-auto flex items-baseline justify-between border-t pt-3">
          <span className="text-base font-bold tabular-nums text-primary">
            {formatPrice(vehicle.list_price_usd)}
          </span>
          {vehicle.vin && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {vehicle.vin.slice(-6)}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
