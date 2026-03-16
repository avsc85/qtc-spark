import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Pencil, Trash2, FileText, Search, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { ContractTemplate, mockTemplates, templateCategories } from "@/lib/mock-data";

const TemplatesPage = () => {
  const [templates, setTemplates] = useState<ContractTemplate[]>(mockTemplates);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ContractTemplate | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [form, setForm] = useState({ name: "", category: "", body: "" });

  const filtered = templates.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.body.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === "all" || t.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const openCreate = () => {
    setEditingTemplate(null);
    setForm({ name: "", category: templateCategories[0], body: "" });
    setDialogOpen(true);
  };

  const openEdit = (t: ContractTemplate) => {
    setEditingTemplate(t);
    setForm({ name: t.name, category: t.category, body: t.body });
    setDialogOpen(true);
  };

  const handleSave = () => {
    if (!form.name.trim() || !form.body.trim()) {
      toast.error("Name and body are required");
      return;
    }

    if (editingTemplate) {
      setTemplates((prev) =>
        prev.map((t) =>
          t.id === editingTemplate.id
            ? { ...t, name: form.name, category: form.category, body: form.body, updated_at: new Date().toISOString().slice(0, 10) }
            : t
        )
      );
      toast.success("Template updated");
    } else {
      const newTemplate: ContractTemplate = {
        id: `tmpl_${Date.now()}`,
        name: form.name,
        category: form.category,
        body: form.body,
        created_at: new Date().toISOString().slice(0, 10),
        updated_at: new Date().toISOString().slice(0, 10),
      };
      setTemplates((prev) => [newTemplate, ...prev]);
      toast.success("Template created");
    }
    setDialogOpen(false);
  };

  const confirmDelete = (id: string) => {
    setDeletingId(id);
    setDeleteDialogOpen(true);
  };

  const handleDelete = () => {
    if (deletingId) {
      setTemplates((prev) => prev.filter((t) => t.id !== deletingId));
      toast.success("Template deleted");
    }
    setDeleteDialogOpen(false);
    setDeletingId(null);
  };

  const grouped = templateCategories.reduce<Record<string, ContractTemplate[]>>((acc, cat) => {
    const items = filtered.filter((t) => t.category === cat);
    if (items.length) acc[cat] = items;
    return acc;
  }, {});

  // If filter is "all", group; otherwise flat list
  const showGrouped = categoryFilter === "all";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Contract Templates</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create and manage reusable contract templates
          </p>
        </div>
        <Button onClick={openCreate} className="gradient-btn gap-2">
          <Plus className="h-4 w-4" /> New Template
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-card border-glass-border"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[180px] bg-card border-glass-border">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {templateCategories.map((c) => (
              <SelectItem key={c} value={c}>{c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Template cards */}
      {filtered.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <FolderOpen className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground">No templates found. Create your first template to get started.</p>
        </div>
      ) : showGrouped ? (
        Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="space-y-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{category}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <AnimatePresence>
                {items.map((t) => (
                  <TemplateCard key={t.id} template={t} onEdit={openEdit} onDelete={confirmDelete} />
                ))}
              </AnimatePresence>
            </div>
          </div>
        ))
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <AnimatePresence>
            {filtered.map((t) => (
              <TemplateCard key={t.id} template={t} onEdit={openEdit} onDelete={confirmDelete} />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl bg-card border-glass-border">
          <DialogHeader>
            <DialogTitle>{editingTemplate ? "Edit Template" : "New Template"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Template Name</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Standard Residential Contract"
                  className="bg-secondary border-glass-border"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Category</label>
                <Select value={form.category} onValueChange={(v) => setForm((f) => ({ ...f, category: v }))}>
                  <SelectTrigger className="bg-secondary border-glass-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {templateCategories.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Contract Body</label>
              <Textarea
                value={form.body}
                onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
                placeholder="Enter the contract template text. Use {{customer}}, {{project_type}}, {{amount}} as placeholders..."
                className="min-h-[250px] bg-secondary border-glass-border font-mono text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} className="gradient-btn">
              {editingTemplate ? "Save Changes" : "Create Template"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md bg-card border-glass-border">
          <DialogHeader>
            <DialogTitle>Delete Template</DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground text-sm">Are you sure you want to delete this template? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const TemplateCard = ({
  template,
  onEdit,
  onDelete,
}: {
  template: ContractTemplate;
  onEdit: (t: ContractTemplate) => void;
  onDelete: (id: string) => void;
}) => (
  <motion.div
    layout
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, scale: 0.95 }}
    className="glass-card-hover p-5 flex flex-col"
  >
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-lg bg-primary/15 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>
        <div>
          <h3 className="font-semibold text-sm leading-tight">{template.name}</h3>
          <span className="text-xs text-muted-foreground">{template.category}</span>
        </div>
      </div>
    </div>
    <p className="text-xs text-muted-foreground line-clamp-3 flex-1 mb-4">
      {template.body.slice(0, 160)}…
    </p>
    <div className="flex items-center justify-between pt-3 border-t border-glass-border">
      <span className="text-xs text-muted-foreground">Updated {template.updated_at}</span>
      <div className="flex gap-1">
        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => onEdit(template)}>
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => onDelete(template.id)}>
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  </motion.div>
);

export default TemplatesPage;
