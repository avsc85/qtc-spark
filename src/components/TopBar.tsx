import { Bell, LogOut, Menu } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

const TopBar = () => {
  return (
    <header className="h-14 flex items-center justify-between border-b border-border px-4">
      <div className="flex items-center gap-3">
        <SidebarTrigger className="text-muted-foreground hover:text-foreground">
          <Menu className="h-5 w-5" />
        </SidebarTrigger>
        <span className="text-sm font-medium text-muted-foreground hidden md:block">
          QTC Construction Management
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <Bell className="h-5 w-5" />
        </Button>
        <Avatar className="h-8 w-8 border border-border">
          <AvatarFallback className="bg-secondary text-secondary-foreground text-xs">JD</AvatarFallback>
        </Avatar>
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
};

export default TopBar;
