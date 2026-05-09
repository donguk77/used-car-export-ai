import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "./layouts/AppLayout";
import { BuyerDetailPage } from "./pages/BuyerDetail";
import { BuyerNewPage } from "./pages/BuyerNew";
import { BuyersPage } from "./pages/Buyers";
import { DashboardPage } from "./pages/Dashboard";
import { DocumentsPage } from "./pages/Documents";
import { ListingDetailPage } from "./pages/ListingDetail";
import { ListingsPage } from "./pages/Listings";
import { MailPage } from "./pages/Mail";
import { NotFoundPage } from "./pages/NotFound";
import { RouteErrorPage } from "./pages/RouteError";
import { SettingsPage } from "./pages/Settings";
import { VehicleDetailPage } from "./pages/VehicleDetail";
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
      { path: "buyers", element: <BuyersPage /> },
      { path: "buyers/new", element: <BuyerNewPage /> },
      { path: "buyers/:id", element: <BuyerDetailPage /> },
      { path: "listings", element: <ListingsPage /> },
      { path: "listings/:id", element: <ListingDetailPage /> },
      { path: "mail", element: <MailPage /> },
      { path: "documents", element: <DocumentsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
