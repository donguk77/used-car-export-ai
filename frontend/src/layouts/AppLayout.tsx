import { useEffect, useRef, useState } from "react";
import {
  Bell,
  Building2,
  Car,
  CheckCircle2,
  Clock,
  FileText,
  Globe2,
  LayoutDashboard,
  Mail,
  Settings as SettingsIcon,
  Users,
  XCircle,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link, NavLink, Outlet } from "react-router-dom";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type NavItem = {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
};

const NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "메인",
    items: [{ label: "대시보드", to: "/", icon: LayoutDashboard }],
  },
  {
    section: "재고 · 거래",
    items: [
      { label: "매물", to: "/vehicles", icon: Car },
      { label: "바이어", to: "/buyers", icon: Users },
      { label: "거래 파이프라인", to: "/listings", icon: FileText },
    ],
  },
  {
    section: "도구",
    items: [
      { label: "다국어 메일", to: "/mail", icon: Mail },
      { label: "수출 서류", to: "/documents", icon: FileText },
    ],
  },
  {
    section: "기타",
    items: [
      { label: "벤치마크 미리보기", to: "/marketplace", icon: Globe2 },
      { label: "설정", to: "/settings", icon: SettingsIcon },
    ],
  },
];

export function AppLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-muted/30">
          <div className="mx-auto max-w-[1400px] px-6 py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r bg-card">
      <div className="flex h-16 items-center gap-2 border-b px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Globe2 className="h-4 w-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">AutoExport AI</span>
          <span className="text-[10px] text-muted-foreground">한양대 ERICA × 하이쓰리디</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {NAV.map((group) => (
          <div key={group.section} className="mb-4">
            <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {group.section}
            </p>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground font-medium"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="border-t p-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
          <Building2 className="h-4 w-4" />
          <div className="flex-1 min-w-0">
            <div className="truncate font-medium text-foreground">동강그린모터스</div>
            <div className="truncate">demo@used-car-export-ai.local</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-base font-semibold text-foreground">중고차 수출 AI 에이전트</h1>
        <span className="rounded-md bg-warning/15 px-2 py-0.5 text-[11px] font-medium text-warning">
          PoC · 단일 사용자 모드
        </span>
      </div>
      <div className="flex items-center gap-3">
        <RecentActivityBell />
      </div>
    </header>
  );
}

interface RecentListing {
  id: string;
  vehicle_label: string;
  buyer_name: string | null;
  destination_country: string | null;
  status: string;
  can_import: boolean | null;
}
interface DashboardSummary {
  recent_listings: RecentListing[];
}

function RecentActivityBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async (): Promise<DashboardSummary> => {
      const r = await api.get<DashboardSummary>("/api/dashboard/summary");
      return r.data;
    },
    staleTime: 30_000,
  });

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    const onPointer = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open]);

  const items = data?.recent_listings ?? [];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((s) => !s)}
        className="relative rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground"
        aria-label="최근 활동"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Bell className="h-4 w-4" />
        {items.length > 0 && (
          <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-primary" />
        )}
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 w-80 rounded-md border bg-card shadow-lg"
        >
          <div className="flex items-center justify-between border-b px-3 py-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              최근 거래
            </p>
            <Link
              to="/listings"
              onClick={() => setOpen(false)}
              className="text-[11px] text-primary hover:underline"
            >
              모두 보기
            </Link>
          </div>
          {isLoading ? (
            <p className="px-3 py-4 text-center text-xs text-muted-foreground">로딩…</p>
          ) : items.length === 0 ? (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              최근 거래가 없습니다
            </p>
          ) : (
            <ul className="max-h-80 overflow-y-auto py-1">
              {items.slice(0, 5).map((it) => (
                <li key={it.id}>
                  <Link
                    to={`/listings/${it.id}`}
                    onClick={() => setOpen(false)}
                    className="flex items-start gap-2.5 px-3 py-2.5 hover:bg-accent"
                  >
                    {it.can_import === false ? (
                      <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                    ) : it.status === "delivered" || it.status === "closed" ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    ) : (
                      <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium">{it.vehicle_label}</p>
                      <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                        {it.buyer_name ?? "—"} · {it.destination_country ?? "—"} · {it.status}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
