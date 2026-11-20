import { cn } from "@/lib/utils";
import * as React from "react";

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-12 w-full rounded-2xl border border-line bg-card px-3 text-base text-ink outline-none ring-green/30 placeholder:text-ink/40 focus:ring-2",
        className,
      )}
      {...props}
    />
  );
}
