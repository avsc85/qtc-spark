import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, FileSignature, Mail, Phone, MapPin } from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import { mockLeads, Lead } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";

const statuses = ["all", "lead", "proposal", "active", "done"];

const LeadsPage = () => {
  const [filter, setFilter] = useState("all");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  const filtered = filter === "all" ? mockLeads : mockLeads.filter((l) => l.status === filter);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Leads</h1>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {statuses.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === s ? "gradient-btn" : "bg-secondary text-secondary-foreground hover:bg-muted"
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Table */}
      <motion.div className="glass-card overflow-hidden" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
                <th className="p-4">Customer</th>
                <th className="p-4">City</th>
                <th className="p-4">Project Type</th>
                <th className="p-4">Quote</th>
                <th className="p-4">Status</th>
                <th className="p-4">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((lead) => (
                <tr
                  key={lead.id}
                  className="hover:bg-secondary/30 transition-colors cursor-pointer"
                  onClick={() => setSelectedLead(lead)}
                >
                  <td className="p-4 font-medium text-sm">{lead.customer}</td>
                  <td className="p-4 text-sm text-muted-foreground">{lead.city}</td>
                  <td className="p-4 text-sm">{lead.project_type}</td>
                  <td className="p-4 text-sm font-medium">${lead.quote_amount.toLocaleString()}</td>
                  <td className="p-4"><StatusBadge status={lead.status} /></td>
                  <td className="p-4 text-sm text-muted-foreground">{lead.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="p-12 text-center text-muted-foreground">
            <p>No leads found with this filter.</p>
          </div>
        )}
      </motion.div>

      {/* Lead Detail Drawer */}
      <AnimatePresence>
        {selectedLead && (
          <>
            <motion.div
              className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedLead(null)}
            />
            <motion.div
              className="fixed right-0 top-0 h-full w-full max-w-md glass-card z-50 border-l border-border overflow-auto"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
            >
              <div className="p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold">{selectedLead.customer}</h2>
                  <Button variant="ghost" size="icon" onClick={() => setSelectedLead(null)}>
                    <X className="h-5 w-5" />
                  </Button>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" /> {selectedLead.city}
                  </div>
                  {selectedLead.email && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Mail className="h-4 w-4" /> {selectedLead.email}
                    </div>
                  )}
                  {selectedLead.phone && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Phone className="h-4 w-4" /> {selectedLead.phone}
                    </div>
                  )}
                </div>

                <div className="glass-card p-4 space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Project Type</span>
                    <span className="font-medium">{selectedLead.project_type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Quote Amount</span>
                    <span className="font-medium">${selectedLead.quote_amount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <StatusBadge status={selectedLead.status} />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Date</span>
                    <span>{selectedLead.date}</span>
                  </div>
                </div>

                {selectedLead.notes && (
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Notes</h3>
                    <p className="text-sm">{selectedLead.notes}</p>
                  </div>
                )}

                <Button className="gradient-btn w-full">
                  <FileSignature className="h-4 w-4 mr-2" /> Generate Contract
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default LeadsPage;
