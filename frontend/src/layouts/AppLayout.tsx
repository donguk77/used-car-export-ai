import {
  Bell,
  Building2,
  Car,
  FileText,
  Globe2,
  LayoutDashboard,
  Mail,
  Settings,
  Users,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

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
    items: [{ label: "설정", to: "/settings", icon: Settings }],
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
        <button
          type="button"
          disabled
          title="알림 — Phase 2 에서 구현"
          className="rounded-md p-2 text-muted-foreground/50 cursor-not-allowed"
          aria-label="알림 (준비중)"
        >
          <Bell className="h-4 w-4" />
        </button>
        <select
          disabled
          title="다국어 UI — Phase 2 에서 구현"
          className="h-8 rounded-md border border-input bg-muted px-2 text-xs text-muted-foreground/60 cursor-not-allowed"
          defaultValue="ko"
          aria-label="언어 (준비중)"
        >
          <option value="ko">한국어</option>
          <option value="en">English</option>
        </select>
      </div>
    </header>
  );
}
