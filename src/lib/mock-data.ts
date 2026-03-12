export interface Lead {
  id: string;
  customer: string;
  city: string;
  project_type: string;
  quote_amount: number;
  status: "lead" | "proposal" | "active" | "done";
  date: string;
  email?: string;
  phone?: string;
  notes?: string;
}

export interface Contract {
  id: string;
  customer: string;
  project_type: string;
  status: "draft" | "sent" | "signed";
  date: string;
  lead_id: string;
  text: string;
}

export interface Invoice {
  id: string;
  milestone: string;
  amount: number;
  due_date: string;
  status: "draft" | "sent" | "paid";
  stripe_link?: string;
  contract_id: string;
  customer: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  action?: { type: string; label: string; data: any };
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  last_message: string;
  date: string;
}

export const mockLeads: Lead[] = [
  { id: "l1", customer: "Marcus Thompson", city: "Austin", project_type: "Kitchen Remodel", quote_amount: 45000, status: "lead", date: "2026-03-10", email: "marcus@email.com", phone: "512-555-0142", notes: "Wants quartz countertops" },
  { id: "l2", customer: "Sarah Chen", city: "Dallas", project_type: "Bathroom Addition", quote_amount: 32000, status: "proposal", date: "2026-03-08", email: "sarah@email.com", phone: "214-555-0198" },
  { id: "l3", customer: "Robert Williams", city: "Houston", project_type: "Deck Build", quote_amount: 18500, status: "active", date: "2026-03-05", email: "rob@email.com" },
  { id: "l4", customer: "Emily Davis", city: "San Antonio", project_type: "Full Renovation", quote_amount: 125000, status: "active", date: "2026-02-28" },
  { id: "l5", customer: "James Rodriguez", city: "Austin", project_type: "Roof Replacement", quote_amount: 22000, status: "done", date: "2026-02-15" },
  { id: "l6", customer: "Angela Martinez", city: "Dallas", project_type: "Window Install", quote_amount: 15000, status: "lead", date: "2026-03-11" },
];

export const mockContracts: Contract[] = [
  { id: "c1", customer: "Sarah Chen", project_type: "Bathroom Addition", status: "draft", date: "2026-03-09", lead_id: "l2", text: "CONSTRUCTION CONTRACT\n\nThis agreement is entered into between QTC Construction LLC and Sarah Chen for the completion of a Bathroom Addition project at the property located in Dallas, TX.\n\nScope of Work:\n- Demolition of existing space\n- New plumbing installation\n- Tile work and finishing\n- Fixture installation\n\nTotal Contract Amount: $32,000\nPayment Schedule: 3 milestones\n\nTimeline: 8 weeks from start date." },
  { id: "c2", customer: "Robert Williams", project_type: "Deck Build", status: "sent", date: "2026-03-06", lead_id: "l3", text: "CONSTRUCTION CONTRACT\n\nThis agreement is between QTC Construction LLC and Robert Williams for a Deck Build project in Houston, TX.\n\nTotal: $18,500\nTimeline: 4 weeks." },
  { id: "c3", customer: "Emily Davis", project_type: "Full Renovation", status: "signed", date: "2026-03-01", lead_id: "l4", text: "CONSTRUCTION CONTRACT\n\nFull renovation contract for Emily Davis. Total: $125,000." },
];

export const mockInvoices: Invoice[] = [
  { id: "i1", milestone: "Demolition Complete", amount: 10000, due_date: "2026-03-15", status: "paid", contract_id: "c3", customer: "Emily Davis" },
  { id: "i2", milestone: "Framing & Rough-In", amount: 35000, due_date: "2026-03-25", status: "sent", contract_id: "c3", customer: "Emily Davis", stripe_link: "https://pay.stripe.com/inv_123" },
  { id: "i3", milestone: "Finish Work", amount: 40000, due_date: "2026-04-10", status: "draft", contract_id: "c3", customer: "Emily Davis" },
  { id: "i4", milestone: "Final Payment", amount: 40000, due_date: "2026-04-25", status: "draft", contract_id: "c3", customer: "Emily Davis" },
  { id: "i5", milestone: "Deposit", amount: 6000, due_date: "2026-03-12", status: "sent", contract_id: "c2", customer: "Robert Williams", stripe_link: "https://pay.stripe.com/inv_456" },
];

export const mockChatSessions: ChatSession[] = [
  { id: "s1", title: "New lead from website", last_message: "I've captured the lead for Marcus Thompson", date: "2026-03-10" },
  { id: "s2", title: "Contract questions", last_message: "The contract has been generated", date: "2026-03-09" },
  { id: "s3", title: "Invoice follow-up", last_message: "Invoice sent to Emily Davis", date: "2026-03-08" },
];

export const mockChatMessages: ChatMessage[] = [
  { id: "m1", role: "user", content: "I got a new lead from my website. Marcus Thompson in Austin wants a kitchen remodel, budget around $45k.", timestamp: "2026-03-10T10:30:00Z" },
  { id: "m2", role: "assistant", content: "I've captured that lead for you. Here's what I recorded:\n\n- **Customer:** Marcus Thompson\n- **City:** Austin\n- **Project:** Kitchen Remodel\n- **Budget:** $45,000\n\nWould you like me to create this lead in the system?", action: { type: "create_lead", label: "Create this lead?", data: { customer: "Marcus Thompson", city: "Austin", project_type: "Kitchen Remodel", quote_amount: 45000 } }, timestamp: "2026-03-10T10:30:05Z" },
];
