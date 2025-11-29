"use client"

import { useRef, useState } from "react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Paperclip, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { IconVideo } from "@tabler/icons-react"
import { createVideo } from "@/infra/videos/videos"

export default function DashboardPage() {
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? [])
    const videoFiles = selected.filter((f) => f.type.startsWith("video"))
    const unique = videoFiles.filter(
      (f) => !files.some((file) => file.name === f.name && file.size === f.size)
    )
    setFiles((prev) => [...prev, ...unique])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files ?? [])
    const videoFiles = droppedFiles.filter((f) => f.type.startsWith("video"))
    const unique = videoFiles.filter(
      (f) => !files.some((file) => file.name === f.name && file.size === f.size)
    )
    setFiles((prev) => [...prev, ...unique])
  }

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleContinue = async () => {
    if (!files.length || isSubmitting) {
      return
    }

    setIsSubmitting(true)
    try {
      await createVideo(files[0])
      router.push(`/dashboard/projects`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex items-center justify-center" style={{ minHeight: "calc(100vh - 3.5rem)" }}>
      <div className="w-full max-w-2xl px-4">

        <div className="text-center mb-12">
          <h1 className="text-4xl text-foreground mb-2">
            <span className="font-semibold">Vídeos longos em{" "}</span>
            <span className="text-emerald-600 font-serif">Clipes Virais</span>
          </h1>
        </div>

        {files.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {files.map((file, idx) => (
              <div
                key={file.name + file.size + idx}
                className="relative group rounded-lg bg-muted p-3 border border-border hover:border-primary transition-colors"
              >
                <div className="flex items-center gap-2">
                  <IconVideo className="h-4 w-4 text-muted-foreground" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground truncate max-w-[120px]">
                      {file.name}
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      {(file.size / (1024 * 1024)).toFixed(1)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  className="absolute -top-2 -right-2 bg-accent text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="space-y-4 flex gap-2">



          <div
            className={cn(
              "relative rounded-full transition-all flex-1",
              isDragging ? "" : "border-border bg-input"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="flex gap-3 items-center px-4 h-12">
              <input
                hidden
                onChange={handleFileChange}
                ref={fileInputRef}
                type="file"
                accept="video/*"
                multiple
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Paperclip className="h-5 w-5" />
              </button>
              <Input
                type="text"
                placeholder="Paste link or drag your video here"
                className="flex-1 focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground"
              />
            </div>
          </div>

          <Button
            className="rounded-full  h-12 font-semibold"
            disabled={!files.length || isSubmitting}
            onClick={handleContinue}
          >
            {isSubmitting ? "Generating clips..." : "Continue"}
          </Button>
        </div>
      </div>
    </div>
  )
}
