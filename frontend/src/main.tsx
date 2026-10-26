import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import Overview from "./pages/Overview";
import Catalog from "./pages/Catalog";
import ColumnDictionary from "./pages/ColumnDictionary";
import Sources from "./pages/Sources";
import TableEditor from "./pages/TableEditor";
import Metrics from "./pages/Metrics";
import Glossary from "./pages/Glossary";
import Settings from "./pages/Settings";
import Quarantine from "./pages/Quarantine";
import PendingChanges from "./pages/PendingChanges";
import Dimensions from "./pages/Dimensions";
import DimensionEditor from "./pages/DimensionEditor";
import NotFound from "./pages/NotFound";
import { AuthProvider } from "./auth";
import { LangProvider, ToastProvider } from "./ui";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false, staleTime: 5000 } } })}>
    <LangProvider>
      <ToastProvider>
       <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Overview />} />
              <Route path="/catalog" element={<Catalog />} />
              <Route path="/tables/:id" element={<TableEditor />} />
              <Route path="/columns" element={<ColumnDictionary />} />
              <Route path="/changes" element={<PendingChanges />} />
              <Route path="/dimensions" element={<Dimensions />} />
              <Route path="/dimensions/:id" element={<DimensionEditor />} />
              <Route path="/quarantine" element={<Quarantine />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/glossary" element={<Glossary />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </BrowserRouter>
       </AuthProvider>
      </ToastProvider>
    </LangProvider>
  </QueryClientProvider>,
);
