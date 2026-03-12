import { motion } from "framer-motion";
import { Send, CheckCircle, ExternalLink } from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import { mockInvoices } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";

const InvoicesPage = () => {
  const total = mockInvoices.reduce((acc, i) => acc + i.amount, 0);
  const paid = mockInvoices.filter((i) => i.status === "paid").reduce((acc, i) => acc + i.amount, 0);

  const handleSend = (id: string) => {
    toast({ title: "Invoice sent!", description: "The invoice has been emailed to the customer." });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Invoices</h1>

      <motion.div className="glass-card overflow-hidden" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
                <th className="p-4">Customer</th>
                <th className="p-4">Milestone</th>
                <th className="p-4">Amount</th>
                <th className="p-4">Due Date</th>
                <th className="p-4">Status</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {mockInvoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-secondary/30 transition-colors">
                  <td className="p-4 text-sm font-medium">{inv.customer}</td>
                  <td className="p-4 text-sm">{inv.milestone}</td>
                  <td className="p-4 text-sm font-medium">${inv.amount.toLocaleString()}</td>
                  <td className="p-4 text-sm text-muted-foreground">{inv.due_date}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      {inv.status === "paid" && <CheckCircle className="h-4 w-4 text-success" style={{ filter: "drop-shadow(0 0 4px hsl(var(--success) / 0.5))" }} />}
                      <StatusBadge status={inv.status} />
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      {inv.status !== "paid" && (
                        <Button size="sm" className="gradient-btn text-xs" onClick={() => handleSend(inv.id)}>
                          <Send className="h-3 w-3 mr-1" /> Send
                        </Button>
                      )}
                      {inv.stripe_link && (
                        <Button size="sm" variant="outline" className="text-xs border-border" asChild>
                          <a href={inv.stripe_link} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-3 w-3 mr-1" /> Stripe
                          </a>
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Total row */}
        <div className="p-4 border-t border-border flex items-center justify-between bg-secondary/20">
          <span className="text-sm text-muted-foreground">
            Paid: <span className="font-medium text-success">${paid.toLocaleString()}</span>
          </span>
          <span className="text-sm font-semibold">
            Total: ${total.toLocaleString()}
          </span>
        </div>
      </motion.div>
    </div>
  );
};

export default InvoicesPage;
