import { cn } from "@/lib/utils";
import * as React from "react";

export function Card({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("rounded-3xl border border-line bg-card p-4 shadow-ticket", className)} {...props} />;
}
