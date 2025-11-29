"use client"

import { use } from "react"
import { AspectRatio } from "@/components/ui/aspect-ratio"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useVideoProgress } from "@/hooks/useVideoProgress"
import { listVideoClips, type VideoClip } from "@/infra/videos/videos"
import { cn } from "@/lib/utils"
import {
  IconCheck,
  IconDownload,
  IconFilter,
  IconPlayerPlayFilled,
  IconPlus,
  IconShare2
} from "@tabler/icons-react"
import { useEffect, useState } from "react"

type ClipsPageProps = {
  params: Promise<{
    videoId: string
  }>
}

export default function ClipsPage({ params }: ClipsPageProps) {
  const { videoId: videoIdStr } = use(params)
  const [clips, setClips] = useState<VideoClip[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [aspectRatio, setAspectRatio] = useState("9:16")
  const videoId = parseInt(videoIdStr, 10) || null
  const { progress, status, error } = useVideoProgress(videoId)

  useEffect(() => {
    async function loadClips() {
      try {
        const items = await listVideoClips(videoId)
        setClips(items)
        if (items.length > 0) {
          setSelectedId(items[0].id)
        }
      } finally {
        setLoading(false)
      }
    }

    loadClips()
  }, [videoId])


  return (
    <section className="flex flex-col h-screen p-10">
      {error && (
        <div className="border-b bg-destructive/10 p-3">
          <p className="text-xs font-medium text-destructive">{error.message}</p>
        </div>
      )}

      {status === "processing" && !error && (
        <div className="border-b p-3">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="text-xs font-medium mb-1">Processando vídeo...</div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <span className="text-xs text-muted-foreground">{progress}%</span>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        {/* Toolbar */}
        <div className="border-b px-6 py-3 flex items-center gap-3 ">
          <Select value={aspectRatio} onValueChange={setAspectRatio}>
            <SelectTrigger className="w-20 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="9:16">9:16</SelectItem>
              <SelectItem value="16:9">16:9</SelectItem>
              <SelectItem value="1:1">1:1</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" className="h-8 gap-2">
            <IconFilter className="h-4 w-4" />
            <span className="text-xs">Filter</span>
          </Button>

          <Select defaultValue="highest">
            <SelectTrigger className="w-40 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="highest">Highest score</SelectItem>
              <SelectItem value="lowest">Lowest score</SelectItem>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="oldest">Oldest</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex-1" />

          <Button variant="outline" size="sm" className="h-8 gap-2">
            <IconCheck className="h-4 w-4" />
            <span className="text-xs">Select all</span>
          </Button>
        </div>

        {/* Content Grid */}
        <div className="overflow-y-auto p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clips.map((clip) => (
              <div
                key={clip.id}
                onClick={() => setSelectedId(clip.id)}
                className={cn(
                  "group cursor-pointer rounded-2xl overflow-hidden border-2 transition-all",
                  selectedId === clip.id
                    ? "border-primary bg-primary/5"
                    : "border-muted hover:border-primary/50"
                )}
              >
                {/* Video Card */}
                <AspectRatio
                  ratio={
                    aspectRatio === "16:9"
                      ? 16 / 9
                      : aspectRatio === "1:1"
                        ? 1
                        : 9 / 16
                  }
                  className="relative bg-black text-white overflow-hidden"
                >
                  <div className="absolute inset-0 flex items-center justify-center">
                    <IconPlayerPlayFilled className="h-16 w-16 opacity-60" />
                  </div>

                  {/* Quality Badge */}
                  <div className="absolute top-3 left-3 bg-black/80 px-2 py-1 rounded text-xs font-medium">
                    720p
                  </div>

                  {/* Duration Badge */}
                  <div className="absolute bottom-3 right-3 bg-black/80 px-2 py-1 rounded text-xs font-medium">
                    01:05
                  </div>

                  {/* Checkbox */}
                  <div className="absolute top-3 right-3">
                    <Checkbox className="bg-white" />
                  </div>
                </AspectRatio>

                {/* Card Content */}
                <div className="p-4 space-y-3">
                  {/* Title & Number */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold line-clamp-2">
                        {clip.title}
                      </h3>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">
                      #{clips.indexOf(clip) + 1}
                    </span>
                  </div>

                  {/* Score */}
                  <div className="flex items-center gap-1">
                    <span className="text-lg font-bold">9.8</span>
                    <span className="text-xs text-muted-foreground">/10</span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-muted-foreground line-clamp-3">
                    O clip mostra o momento 'mágico' em que o agente de navegador, após receber instruções complexas, acessa e valida o localhost, provando sua capacidade de operar fora do ambiente do código.
                  </p>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-2">
                    <Button size="sm" className="flex-1 gap-2 h-8">
                      <span className="text-xs">Publish</span>
                    </Button>
                    <Button variant="outline" size="sm" className="h-8">
                      <IconDownload className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" className="h-8">
                      <IconShare2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Add Button */}
                  <Button variant="outline" size="sm" className="w-full h-8 gap-2 text-xs">
                    <IconPlus className="h-4 w-4" />
                    <span>Add to collection</span>
                  </Button>
                </div>
              </div>
            ))}

            {!loading && clips.length === 0 && (
              <div className="col-span-full flex items-center justify-center py-12">
                <p className="text-sm text-muted-foreground">Nenhum clip gerado ainda.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
