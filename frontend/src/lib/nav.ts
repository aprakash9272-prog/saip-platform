import type { LucideIcon } from "lucide-react";
import {
  Blocks,
  Boxes,
  Building2,
  Layers,
  LayoutDashboard,
  Library,
  ListChecks,
  Network,
  Package,
  ShieldCheck,
  Tags,
} from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
}

export interface NavGroup extends NavItem {
  children?: NavItem[];
}

export const NAV_ITEMS: NavGroup[] = [
  {
    title: "Home",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Customers",
    href: "/customers",
    icon: Building2,
  },
  {
    title: "Knowledge Base",
    href: "/knowledge-base",
    icon: Library,
    children: [
      { title: "Vendors", href: "/knowledge-base/vendors", icon: Building2 },
      { title: "Products", href: "/knowledge-base/products", icon: Package },
      { title: "Editions", href: "/knowledge-base/editions", icon: Layers },
      { title: "Modules", href: "/knowledge-base/modules", icon: Blocks },
      { title: "Domains", href: "/knowledge-base/domains", icon: Tags },
      {
        title: "Capabilities",
        href: "/knowledge-base/capabilities",
        icon: ShieldCheck,
      },
      { title: "Frameworks", href: "/knowledge-base/frameworks", icon: ListChecks },
      { title: "Mappings", href: "/knowledge-base/mappings", icon: Boxes },
      {
        title: "Product Mappings",
        href: "/knowledge-base/product-mappings",
        icon: Network,
      },
    ],
  },
];
