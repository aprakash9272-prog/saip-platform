"use client";

import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/lib/nav";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";

function useCurrentPageTitle(): string {
  const pathname = usePathname();
  const flat = NAV_ITEMS.flatMap((item) => [item, ...(item.children ?? [])]);
  const match = flat
    .filter((item) => (item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)))
    .sort((a, b) => b.href.length - a.href.length)[0];
  return match?.title ?? "Dashboard";
}

export function SiteHeader() {
  const title = useCurrentPageTitle();

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      <h1 className="text-sm font-medium">{title}</h1>
      <div className="ml-auto flex items-center gap-3">
        <Avatar className="size-8">
          <AvatarFallback>SA</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
