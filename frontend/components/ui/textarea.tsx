import { cn } from "@/lib/utils";
import * as React from "react";

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "min-h-24 w-full rounded-2xl border border-line bg-card px-3 py-3 text-base text-ink outline-none ring-green/30 placeholder:text-ink/40 focus:ring-2",
        className,
      )}
      {...props}
    />
  );
}
