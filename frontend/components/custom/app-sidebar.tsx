"use client"

import * as React from "react"
import {
  BookOpen,
  Bot,
  Rocket,
  Settings2,
  SquareTerminal,
  Terminal,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail
} from "@/components/ui/sidebar"
import { NavMain } from "./nav-main"
import { DropdownMenu, DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu"
import { Button } from "../ui/button"
import Link from "next/link"


const data = {
  navMain: [
    {
      title: "Playground",
      url: "playground",
      icon: SquareTerminal
    },
    {
      title: "Models",
      url: "models",
      icon: Bot
    },
    {
      title: "CLI",
      url: "cli",
      icon: Terminal
    },
    {
      title: "Documentation",
      url: "#",
      icon: BookOpen,
      items: [
        {
          title: "Introduction",
          url: "#",
        },
        {
          title: "Get Started",
          url: "#",
        },
        {
          title: "Tutorials",
          url: "#",
        },
        {
          title: "Changelog",
          url: "#",
        },
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      items: [
        {
          title: "General",
          url: "#",
        },
        {
          title: "Team",
          url: "#",
        },
        {
          title: "Billing",
          url: "#",
        },
        {
          title: "Limits",
          url: "#",
        },
      ],
    },
  ],
  chats: [
    {
      name: "Ethical Issues",
      url: "#",
    },
    {
      name: "Ability to Minimize Bias",
      url: "#",
    },
    {
      name: "Psacebo-controlled",
      url: "#",
    },
  ],
}


export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Link href={"/"}>
                    <SidebarMenuButton
                        size="lg"
                        className=""
                      >
                        <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                            <Rocket className="size-4" />
                        </div>
                        <div className="grid flex-1 text-left text-sm leading-tight">
                            <span className="truncate font-medium">MiniRag</span>
                            <span className="truncate text-xs">Mini, yet regorous</span>
                        </div>
                    </SidebarMenuButton>
                  </Link>
          </DropdownMenuTrigger>
        </DropdownMenu>
      </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} chats={data.chats}/>
      </SidebarContent>
      <SidebarFooter>
        <Button variant={"destructive"}>Challenge MiniRag 😏️</Button>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
