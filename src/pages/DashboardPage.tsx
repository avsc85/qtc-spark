import { motion } from "framer-motion";
import { Users, FileText, Receipt, DollarSign, Plus, FileSignature, Send } from "lucide-react";
import AnimatedCounter from "@/components/AnimatedCounter";
import StatusBadge from "@/components/StatusBadge";
import { mockLeads, mockInvoices } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const stats = [
  { label: "Total Leads", value: 24, icon: Users, color: "from-primary to-blue-400" },
  { label: "Active Contracts", value: 8, icon: FileText, color: "from-accent to-purple-400" },
  { label: "Unpaid Invoices", value: 5, icon: Receipt, color: "from-warning to-amber-400" },
  { label: "Revenue (MTD)", value: 142000, icon: DollarSign, prefix: "$", color: "from-success to-emerald-400" },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const DashboardPage = () => {
  const navigate = useNavigate();

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back. Here's your overview.</p>
        </div>
        <div className="flex gap-2">
          <Button className="gradient-btn" onClick={() => navigate("/leads")}>
            <Plus className="h-4 w-4 mr-2" /> New Lead
          </Button>
          <Button variant="outline" className="border-border" onClick={() => navigate("/contracts")}>
            <FileSignature className="h-4 w-4 mr-2" /> Generate Contract
          </Button>
          <Button variant="outline" className="border-border" onClick={() => navigate("/invoices")}>
            <Send className="h-4 w-4 mr-2" /> Send Invoice
          </Button>
        </div>
      </div>

      {/* Stats */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {stats.map((stat) => (
          <motion.div key={stat.label} variants={item} className="glass-card-hover p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">{stat.label}</span>
              <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="h-4 w-4 text-primary-foreground" />
              </div>
            </div>
            <div className="text-2xl font-bold">
              <AnimatedCounter value={stat.value} prefix={stat.prefix} />
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Recent Leads & Invoices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="font-semibold">Recent Leads</h2>
            <Button variant="ghost" size="sm" className="text-primary" onClick={() => navigate("/leads")}>
              View all
            </Button>
          </div>
          <div className="divide-y divide-border">
            {mockLeads.slice(0, 4).map((lead) => (
              <div key={lead.id} className="p-4 flex items-center justify-between hover:bg-secondary/30 transition-colors cursor-pointer" onClick={() => navigate("/leads")}>
                <div>
                  <p className="font-medium text-sm">{lead.customer}</p>
                  <p className="text-xs text-muted-foreground">{lead.project_type} • {lead.city}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">${lead.quote_amount.toLocaleString()}</span>
                  <StatusBadge status={lead.status} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="font-semibold">Recent Invoices</h2>
            <Button variant="ghost" size="sm" className="text-primary" onClick={() => navigate("/invoices")}>
              View all
            </Button>
          </div>
          <div className="divide-y divide-border">
            {mockInvoices.slice(0, 4).map((inv) => (
              <div key={inv.id} className="p-4 flex items-center justify-between hover:bg-secondary/30 transition-colors cursor-pointer" onClick={() => navigate("/invoices")}>
                <div>
                  <p className="font-medium text-sm">{inv.milestone}</p>
                  <p className="text-xs text-muted-foreground">{inv.customer} • Due {inv.due_date}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">${inv.amount.toLocaleString()}</span>
                  <StatusBadge status={inv.status} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default DashboardPage;
