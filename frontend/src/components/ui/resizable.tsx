import { GripVertical } from "lucide-react"
import { Group, Panel, Separator } from "react-resizable-panels"
import type { ComponentProps } from "react"

import { cn } from "@/lib/utils"

function ResizablePanelGroup({
  className,
  ...props
}: ComponentProps<typeof Group>) {
  return (
    <Group
      className={cn(
        "flex h-full w-full",
        className
      )}
      {...props}
    />
  )
}

const ResizablePanel = Panel

function ResizableHandle({
  withHandle,
  className,
  ...props
}: ComponentProps<typeof Separator> & {
  withHandle?: boolean
}) {
  return (
    <Separator
      className={cn(
        "relative flex w-1 items-center justify-center bg-gray-700 hover:bg-purple-600 transition-colors",
        "after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2",
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-purple-500",
        "[&[aria-orientation=vertical]]:h-1 [&[aria-orientation=vertical]]:w-full",
        "[&[aria-orientation=vertical]]:after:left-0 [&[aria-orientation=vertical]]:after:h-1",
        "[&[aria-orientation=vertical]]:after:w-full [&[aria-orientation=vertical]]:after:-translate-y-1/2",
        "[&[aria-orientation=vertical]]:after:translate-x-0",
        "[&[aria-orientation=vertical]>div]:rotate-90",
        className
      )}
      {...props}
    >
      {withHandle && (
        <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border border-gray-600 bg-gray-700 hover:bg-purple-600 hover:border-purple-500 transition-colors">
          <GripVertical className="h-2.5 w-2.5 text-gray-400" />
        </div>
      )}
    </Separator>
  )
}

export { ResizablePanelGroup, ResizablePanel, ResizableHandle }
