import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("bg-accent rounded-md animate-[pulse_6s_ease-in-out_infinite]", className)}
      {...props}
    />
  )
}

export { Skeleton }