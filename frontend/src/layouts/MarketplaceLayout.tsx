import { useState } from "react";
import { ChevronDown, Globe, Menu, MessageCircle, Search, ShoppingBag, User } from "lucide-react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { DemoModeModal } from "@/components/marketplace/DemoModeModal";
import { cn } from "@/lib/utils";

/** Autobell Global 스타일 마켓플레이스 레이아웃 (벤치마크용).
 *  상단 가로 네비 + 다국어 + 지역 에이전트 + 풋터.
 *  — 우리 admin app(/) 와 별도 시각으로 멘토 비교용. */
export function MarketplaceLayout() {
  const [demoFeature, setDemoFeature] = useState<string | null>(null);
  const showDemo = (feature: string) => setDemoFeature(feature);

  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900">
      <BenchmarkBanner />
      <TopBar onDemo={showDemo} />
      <MainNav onDemo={showDemo} />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <DemoModeModal
        open={Boolean(demoFeature)}
        feature={demoFeature ?? ""}
        onClose={() => setDemoFeature(null)}
      />
    </div>
  );
}

function BenchmarkBanner() {
  return (
    <div className="bg-amber-50 px-4 py-1.5 text-center text-[11px] text-amber-800">
      벤치마크 비교용 화면 — Autobell Global 스타일 모방.{" "}
      <Link to="/" className="font-semibold underline hover:text-amber-900">
        ↩ 우리 admin SaaS 로 돌아가기
      </Link>
    </div>
  );
}

function TopBar({ onDemo }: { onDemo: (feature: string) => void }) {
  return (
    <div className="border-b bg-slate-50">
      <div className="mx-auto flex h-9 max-w-[1400px] items-center justify-between px-4 sm:px-6 text-xs text-slate-600">
        <div className="hidden sm:block">
          Free 112-point inspection · Warranty available · Worldwide delivery
        </div>
        <div className="flex items-center gap-3 sm:gap-4">
          <button type="button" onClick={() => onDemo("Language / 다국어 전환")} className="flex items-center gap-1 hover:text-slate-900">
            <Globe className="h-3 w-3" />
            English <ChevronDown className="h-3 w-3" />
          </button>
          <span className="hidden text-slate-300 sm:inline">|</span>
          <button type="button" onClick={() => onDemo("Regional Agents")} className="hidden items-center gap-1 hover:text-slate-900 sm:flex">
            Regional Agents <ChevronDown className="h-3 w-3" />
          </button>
          <span className="hidden text-slate-300 sm:inline">|</span>
          <button type="button" onClick={() => onDemo("WhatsApp 상담")} className="flex items-center gap-1 hover:text-slate-900">
            <MessageCircle className="h-3 w-3" /> WhatsApp
          </button>
        </div>
      </div>
    </div>
  );
}

function MainNav({ onDemo }: { onDemo: (feature: string) => void }) {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/marketplace" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-slate-900 text-white">
            <span className="text-sm font-bold tracking-tighter">AE</span>
          </div>
          <div className="leading-tight">
            <div className="text-base font-bold tracking-tight">AutoExport Global</div>
            <div className="hidden text-[10px] uppercase tracking-widest text-slate-500 sm:block">
              Korean Used Cars
            </div>
          </div>
        </Link>

        {/* Desktop nav — Used Car 만 라우팅, 나머지는 Phase 2 표시 */}
        <nav className="hidden items-center gap-8 text-sm md:flex">
          <NavLink
            to="/marketplace/catalog"
            className={({ isActive }) =>
              cn(
                "py-1 font-medium transition-colors",
                isActive
                  ? "border-b-2 border-slate-900 text-slate-900"
                  : "text-slate-600 hover:text-slate-900",
              )
            }
          >
            Used Car
          </NavLink>
          {["Auction", "Inspection", "About AutoExport"].map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => onDemo(label)}
              className="py-1 font-medium text-slate-600 hover:text-slate-900"
            >
              {label}
            </button>
          ))}
        </nav>

        {/* Desktop right cluster */}
        <div className="hidden items-center gap-3 md:flex">
          <button
            type="button"
            onClick={() => onDemo("Search / 통합 검색")}
            className="rounded-md p-2 text-slate-600 hover:bg-slate-100"
            aria-label="Search"
          >
            <Search className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => onDemo("My Order")}
            className="flex items-center gap-1.5 rounded-md p-2 text-sm text-slate-600 hover:bg-slate-100"
          >
            <ShoppingBag className="h-4 w-4" /> My Order
          </button>
          <button
            type="button"
            onClick={() => onDemo("Log In / Sign Up")}
            className="flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            <User className="h-4 w-4" /> Log In
          </button>
        </div>

        {/* Mobile hamburger (placeholder — Phase 2 에서 drawer 구현) */}
        <button
          type="button"
          disabled
          aria-label="Menu (mobile drawer — coming soon)"
          title="모바일 메뉴 — Phase 2"
          className="rounded-md p-2 text-slate-400 md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-12 bg-slate-900 text-slate-300">
      <div className="mx-auto grid max-w-[1400px] grid-cols-2 gap-8 px-6 py-12 sm:grid-cols-4">
        <div className="col-span-2 sm:col-span-1">
          <div className="mb-3 text-base font-bold text-white">AutoExport Global</div>
          <p className="text-xs leading-relaxed text-slate-400">
            Korean used car export platform. Inspected · Warranted · Globally shipped.
          </p>
        </div>
        <FooterCol
          title="Used Cars"
          items={["View All", "Stock", "Auction", "Condition Reported", "Warranty Available"]}
        />
        <FooterCol
          title="Company"
          items={["About AutoExport", "Inspection Center", "Terms of Use", "Privacy Policy"]}
        />
        <FooterCol
          title="Customer Center"
          items={["FAQ", "Contact", "Regional Agents", "WhatsApp"]}
        />
      </div>
      <div className="border-t border-slate-800">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-2 px-6 py-4 text-[11px] text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <div>© 2026 AutoExport Global · Capstone PoC · 한양대 ERICA × ㈜하이쓰리디</div>
          <div className="flex gap-3">
            <a href="#" className="hover:text-slate-300">Terms</a>
            <a href="#" className="hover:text-slate-300">Privacy</a>
            <a href="#" className="hover:text-slate-300">Warranty</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-200">
        {title}
      </div>
      <ul className="space-y-1.5 text-xs">
        {items.map((item) => (
          <li key={item}>
            <a href="#" className="text-slate-400 hover:text-white">
              {item}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
