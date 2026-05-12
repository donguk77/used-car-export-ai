import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./layouts/AppLayout";
import { MarketplaceLayout } from "./layouts/MarketplaceLayout";
import { BuyerDetailPage } from "./pages/BuyerDetail";
import { BuyerNewPage } from "./pages/BuyerNew";
import { BuyersPage } from "./pages/Buyers";
import { DashboardPage } from "./pages/Dashboard";
import { DocumentsPage } from "./pages/Documents";
import { ListingDetailPage } from "./pages/ListingDetail";
import { ListingsPage } from "./pages/Listings";
import { MailPage } from "./pages/Mail";
import { MarketplaceCatalog } from "./pages/marketplace/MarketplaceCatalog";
import { MarketplaceLanding } from "./pages/marketplace/MarketplaceLanding";
import { MarketplaceVehicleDetail } from "./pages/marketplace/MarketplaceVehicleDetail";
import { NotFoundPage } from "./pages/NotFound";
import { RouteErrorPage } from "./pages/RouteError";
import { SettingsPage } from "./pages/Settings";
import { VehicleDetailPage } from "./pages/VehicleDetail";
import { VehicleEditPage } from "./pages/VehicleEdit";
import { VehicleNewPage } from "./pages/VehicleNew";
import { VehiclesPage } from "./pages/Vehicles";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "vehicles", element: <VehiclesPage /> },
      { path: "vehicles/new", element: <VehicleNewPage /> },
      { path: "vehicles/:id", element: <VehicleDetailPage /> },
      { path: "vehicles/:id/edit", element: <VehicleEditPage /> },
      { path: "buyers", element: <BuyersPage /> },
      { path: "buyers/new", element: <BuyerNewPage /> },
      { path: "buyers/:id", element: <BuyerDetailPage /> },
      { path: "listings", element: <ListingsPage /> },
      { path: "listings/:id", element: <ListingDetailPage /> },
      { path: "mail", element: <MailPage /> },
      { path: "documents", element: <DocumentsPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
  // Marketplace 벤치마크 (Autobell-style) — 멘토 비교용 별도 레이아웃
  {
    path: "/marketplace",
    element: <MarketplaceLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <MarketplaceLanding /> },
      { path: "catalog", element: <MarketplaceCatalog /> },
      { path: ":id", element: <MarketplaceVehicleDetail /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
