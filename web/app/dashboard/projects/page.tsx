"use client"

import { IconDots, IconEdit, IconTrash } from "@tabler/icons-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { listVideos, type Video } from "@/infra/videos/videos"

type VideoWithProgress = Video & {
  progress?: number
  processingStatus?: "processing" | "completed"
}

export default function ProjectsPage() {
  const [query, setQuery] = useState("")
  const [videos, setVideos] = useState<VideoWithProgress[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadVideos() {
      try {
        const items = await listVideos()
        setVideos(items as VideoWithProgress[])
      } finally {
        setLoading(false)
      }
    }

    loadVideos()
    const interval = setInterval(loadVideos, 2000)
    return () => clearInterval(interval)
  }, [])

  const filteredVideos = useMemo(() => {
    return videos.filter((video) =>
      video.title.toLowerCase().includes(query.toLowerCase())
    )
  }, [videos, query])

  return (
    <section className="flex flex-col gap-6 p-10">

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          <div className="col-span-full text-center text-muted-foreground">Carregando vídeos...</div>
        ) : filteredVideos.length === 0 ? (
          <div className="col-span-full text-center text-muted-foreground">Nenhum vídeo encontrado</div>
        ) : (
          filteredVideos.map((video) => (
            <article
              key={video.id}
              className="group relative rounded-2xl border bg-card overflow-hidden shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="relative h-40 overflow-hidden">
                <div className="absolute inset-0 bg-black/20" />
                {video.status === "processing" && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">{video.progress || 0}%</div>
                      <div className="text-xs text-white/80">Processando...</div>
                    </div>
                  </div>
                )}
                {video.status === "completed" && (
                  <div className="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                    <Button size="sm" className="rounded-full">
                      Ver clips
                    </Button>
                  </div>
                )}
              </div>

              <div className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h2 className="text-lg font-semibold line-clamp-2">{video.title}</h2>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="p-1 rounded-lg hover:bg-muted opacity-0 group-hover:opacity-100 transition-all pointer-events-auto">
                            <IconDots className="h-4 w-4 text-muted-foreground" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="pointer-events-auto">
                          <DropdownMenuItem>
                            <IconEdit className="mr-2 h-4 w-4" />
                            Renomear
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive focus:text-destructive">
                            <IconTrash className="mr-2 h-4 w-4" />
                            Deletar
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>

                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <div>Status: {video.status}</div>
                  {video.status === "processing" && (
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className="bg-primary h-1.5 rounded-full transition-all"
                        style={{ width: `${video.progress || 0}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
