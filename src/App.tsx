import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "@/components/AppLayout";
import DashboardPage from "@/pages/DashboardPage";
import LeadsPage from "@/pages/LeadsPage";
import ContractsPage from "@/pages/ContractsPage";
import InvoicesPage from "@/pages/InvoicesPage";
import ChatPage from "@/pages/ChatPage";
import ESignPage from "@/pages/ESignPage";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/sign/:token" element={<ESignPage />} />
          <Route
            path="*"
            element={
              <AppLayout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/leads" element={<LeadsPage />} />
                  <Route path="/contracts" element={<ContractsPage />} />
                  <Route path="/invoices" element={<InvoicesPage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </AppLayout>
            }
          />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
