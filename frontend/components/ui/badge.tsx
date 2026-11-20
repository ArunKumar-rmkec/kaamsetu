import { cn } from "@/lib/utils";
import * as React from "react";

export function Badge({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-semibold text-ink",
        className,
      )}
      {...props}
    />
  );
}
