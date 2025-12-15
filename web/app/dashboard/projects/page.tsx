"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { listVideos, deleteVideo } from "@/infra/videos/videos"
import { Video } from "@/infra/videos/types/videos-types"
import { Spinner } from "@/components/ui/spinner"
import { HugeiconsIcon } from "@hugeicons/react"
import { MoreHorizontalIcon, ScissorIcon, Delete02Icon, FilterIcon } from "@hugeicons/core-free-icons"

export default function ProjectsPage() {
  const router = useRouter()
  const [videos, setVideos] = useState<Video[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedVideos, setSelectedVideos] = useState<number[]>([])

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const data = await listVideos()
        setVideos(data)
      } catch (error) {
        console.error("Error fetching videos:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchVideos()
  }, [])

  const handleDeleteSelected = async () => {
    try {
      await Promise.all(selectedVideos.map(deleteVideo))
      const data = await listVideos()
      setVideos(data)
      setSelectedVideos([])
    } catch (error) {
      console.error("Error deleting videos:", error)
    }
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedVideos(videos.map((video) => video.id))
    } else {
      setSelectedVideos([])
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("pt-BR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const formatDuration = (seconds: number | undefined) => {
    if (seconds === undefined) return "00:00";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-primary"
      case "processing":
        return "text-orange-500"
      case "failed":
        return "text-destructive"
      default:
        return "text-muted-foreground"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "Concluído"
      case "processing":
        return "Processando..."
      case "failed":
        return "Erro"
      case "pending":
        return "Pendente"
      default:
        return status
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col">
        <h1 className="text-2xl text-foreground p-12">Projetos</h1>
        <div className="flex-1 flex items-center justify-center">
          <Spinner />
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-12 overflow-y-auto relative">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl text-foreground">Projetos</h1>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="h-9 text-zinc-300 hover:bg-zinc-800 hover:text-white gap-2 text-xs"
          >
            <HugeiconsIcon icon={FilterIcon} className="h-4 w-4" />
            <span>Filtrar</span>
          </Button>
          <div className="flex bg-card items-center gap-2 rounded-md px-3 h-9">
            <span className="text-xs text-zinc-300">Selecionar Tudo</span>
            <Checkbox
              checked={selectedVideos.length === videos.length && videos.length > 0}
              onCheckedChange={handleSelectAll}
            />
          </div>
        </div>
      </div>

      {videos.length === 0 ? (
        <div className="text-muted-foreground">Nenhum projeto encontrado</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {videos.map((video) => (
            <div
              key={video.id}
              onClick={() => router.push(`/clips/${video.id}`)}
              className="group relative bg-card rounded-md overflow-hidden transition-colors cursor-pointer hover:border-primary/50"
            >
              <div className="bg-muted relative">
                {video.thumbnail ? (
                  <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-muted" />
                )}

                {video.duration && (
                  <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md">
                    {formatDuration(video.duration)}
                  </div>
                )}

                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <div className="bg-muted px-3 py-1.5 rounded-md flex items-center gap-2 text-xs font-medium border border-border text-foreground">
                    <span className="text-muted-foreground">{video.clips?.length || 0}</span> Clips
                  </div>
                  <div className="bg-muted p-1.5 rounded-md border border-border text-foreground">
                    <HugeiconsIcon icon={ScissorIcon} size={16} />
                  </div>
                </div>

                <div
                  className={cn(
                    "absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100",
                    selectedVideos.includes(video.id) && "opacity-100"
                  )}
                  onClick={(e) => e.stopPropagation()}
                >
                  <Checkbox
                    checked={selectedVideos.includes(video.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedVideos([...selectedVideos, video.id])
                      } else {
                        setSelectedVideos(
                          selectedVideos.filter((id) => id !== video.id)
                        )
                      }
                    }}
                  />
                </div>
              </div>

              <div className="p-4">
                <div className="text-xs text-muted-foreground mb-1">{formatDate(video.created_at)}</div>
                <h3 className="font-medium text-sm text-foreground mb-2 truncate">{video.title}</h3>
                <div className="flex items-center justify-between mt-4">
                  <span className={`text-xs ${getStatusColor(video.status)}`}>
                    {getStatusLabel(video.status)}
                  </span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className="text-muted-foreground hover:text-foreground transition-colors" onClick={(e) => e.stopPropagation()}>
                        <HugeiconsIcon icon={MoreHorizontalIcon} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>Ver detalhes</DropdownMenuItem>
                      <DropdownMenuItem>Editar</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive">Deletar</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedVideos.length > 0 && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-card border rounded-md shadow-lg p-2 flex items-center gap-4 animate-in slide-in-from-bottom-5">
          <span className="text-sm font-medium pl-2">
            {selectedVideos.length} selected
          </span>
          <Button variant="destructive" size="sm" onClick={handleDeleteSelected}>
            <HugeiconsIcon icon={Delete02Icon} className="size-4 mr-2" />
            Delete
          </Button>
        </div>
      )}
    </div>
  )
}
