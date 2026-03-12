import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, X, Download, Edit } from "lucide-react";
import StatusBadge from "@/components/StatusBadge";
import { mockContracts, Contract } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } };

const ContractsPage = () => {
  const [selected, setSelected] = useState<Contract | null>(null);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Contracts</h1>

      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {mockContracts.map((contract) => (
          <motion.div
            key={contract.id}
            variants={item}
            className="glass-card-hover p-5 cursor-pointer"
            onClick={() => setSelected(contract)}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold">{contract.customer}</h3>
                <p className="text-sm text-muted-foreground">{contract.project_type}</p>
              </div>
              <StatusBadge status={contract.status} />
            </div>
            <p className="text-xs text-muted-foreground mb-4">{contract.date}</p>
            {contract.status === "draft" && (
              <Button size="sm" className="gradient-btn w-full" onClick={(e) => { e.stopPropagation(); }}>
                <Send className="h-3 w-3 mr-2" /> Send for Signing
              </Button>
            )}
          </motion.div>
        ))}
      </motion.div>

      {mockContracts.length === 0 && (
        <div className="glass-card p-12 text-center text-muted-foreground">
          <p>No contracts yet — generate one from a lead.</p>
        </div>
      )}

      {/* Contract Viewer Modal */}
      <Dialog open={!!selected} onOpenChange={() => setSelected(null)}>
        <DialogContent className="max-w-2xl bg-card border-border">
          <DialogHeader>
            <DialogTitle>{selected?.customer} — {selected?.project_type}</DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-96 overflow-auto rounded-lg bg-secondary/30 p-6">
            <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{selected?.text}</pre>
          </div>
          <div className="flex gap-2 mt-4">
            <Button variant="outline" className="border-border">
              <Edit className="h-4 w-4 mr-2" /> Edit
            </Button>
            <Button variant="outline" className="border-border">
              <Download className="h-4 w-4 mr-2" /> Download PDF
            </Button>
            {selected?.status === "draft" && (
              <Button className="gradient-btn ml-auto">
                <Send className="h-4 w-4 mr-2" /> Send for Signing
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ContractsPage;
