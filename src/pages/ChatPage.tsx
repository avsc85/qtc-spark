import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Mic, Sparkles, Plus, MessageSquare, Check } from "lucide-react";
import { mockChatSessions, mockChatMessages, ChatMessage } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";

const ChatPage = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessages);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [activeSession, setActiveSession] = useState("s1");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = {
      id: `m${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    // Simulate streaming response
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: `m${Date.now() + 1}`,
        role: "assistant",
        content: "I understand you'd like help with that. Let me look into it and get back to you with the details.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
      setStreaming(false);
    }, 1500);
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {/* Session Sidebar */}
      <div className="w-64 border-r border-border flex-col hidden md:flex">
        <div className="p-3 border-b border-border">
          <Button size="sm" className="gradient-btn w-full text-xs">
            <Plus className="h-3 w-3 mr-2" /> New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-2 space-y-1">
          {mockChatSessions.map((session) => (
            <button
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${
                activeSession === session.id
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-secondary/50"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <MessageSquare className="h-3 w-3 shrink-0" />
                <span className="font-medium truncate">{session.title}</span>
              </div>
              <p className="text-xs truncate text-muted-foreground">{session.last_message}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-auto p-6 space-y-4">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-lg rounded-2xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "gradient-btn rounded-br-md"
                    : "glass-card rounded-bl-md"
                }`}
              >
                <div className="prose prose-sm prose-invert max-w-none [&>p]:mb-1 [&>ul]:mt-1">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {/* Action Card */}
                {msg.action && (
                  <div className="mt-3 p-3 rounded-lg bg-secondary/50 border border-border">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="h-4 w-4 text-primary" />
                      <span className="text-xs font-medium">{msg.action.label}</span>
                    </div>
                    <Button size="sm" className="gradient-btn text-xs w-full">
                      <Check className="h-3 w-3 mr-1" /> Confirm
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {streaming && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="glass-card rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: "0.2s" }} />
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <div className="flex-1 glass-card flex items-center px-4">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask QTC anything..."
                className="flex-1 bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
              />
              <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground shrink-0">
                <Mic className="h-4 w-4" />
              </Button>
            </div>
            <Button className="gradient-btn px-4" onClick={handleSend} disabled={!input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
