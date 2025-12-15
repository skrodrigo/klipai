"use client"

import { use, useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { HugeiconsIcon } from "@hugeicons/react"
import { ArrowLeft02Icon, Download01Icon, FilterIcon, PlayIcon, Share03Icon, Edit02Icon, Copy01Icon, Delete02Icon, SentIcon, ScissorIcon, Upload04Icon, GlobeIcon, LockIcon } from "@hugeicons/core-free-icons"
import { listVideoClips, type VideoClip } from "@/infra/videos/videos"
import { Spinner } from "@/components/ui/spinner"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"

type ClipsPageProps = {
  params: Promise<{
    videoId: string
  }>
}

export default function ClipsPage({ params }: ClipsPageProps) {
  const router = useRouter()
  const { videoId: videoIdStr } = use(params)
  const [clips, setClips] = useState<VideoClip[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [publishOpen, setPublishOpen] = useState(false)
  const [description, setDescription] = useState("")
  const [visibility, setVisibility] = useState<"public" | "private" | "friends">("public")
  const [allowComments, setAllowComments] = useState(true)
  const [allowDuets, setAllowDuets] = useState(true)
  const [allowStitch, setAllowStitch] = useState(true)
  const [scheduleAt, setScheduleAt] = useState("")
  const [isDialogOpen, setDialogOpen] = useState(false)
  const videoId = parseInt(videoIdStr, 10) || null
  const [value, setValue] = useState<"public" | "private">("private")
  const [showTopFade, setShowTopFade] = useState(false)
  const [showBottomFade, setShowBottomFade] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const handleClipSelect = (clipId: number, idx: number) => {
    setSelectedIdx(idx)
    const element = document.getElementById(`clip-${clipId}`)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" })
    }
  }

  useEffect(() => {
    async function loadClips() {
      try {
        const items = await listVideoClips(videoId)
        setClips(items)
      } finally {
        setLoading(false)
      }
    }

    loadClips()
  }, [videoId])

  useEffect(() => {
    const scrollElement = scrollRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]",
    )

    if (!scrollElement) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollElement
      setShowTopFade(scrollTop > 0)
      setShowBottomFade(scrollTop + clientHeight < scrollHeight - 1)
    }

    handleScroll()
    scrollElement.addEventListener("scroll", handleScroll)
    return () => scrollElement.removeEventListener("scroll", handleScroll)
  }, [clips])


  return (
    <div className="w-full h-screen flex flex-col bg-background text-foreground relative">
      <Button
        onClick={() => router.back()}
        variant='ghost'
        className="absolute fixed top-6 left-6 flex items-center gap-2 text-foreground hover:text-foreground text-sm z-10"
      >
        <HugeiconsIcon icon={ArrowLeft02Icon} strokeWidth={2} />
        Voltar
      </Button>

      {loading ? (
        <div className="flex flex-col p-12">
          <div className="flex-1 flex items-center justify-center">
            <Spinner />
          </div>
        </div>
      ) : (
        <div className="flex-1 flex">
          {/* Left Sidebar - Clips List */}
          <aside className="w-80 fixed inset-y-0 hidden lg:flex shrink-0 items-center">
            <div className="relative w-full">
              {showTopFade && (
                <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-background to-transparent z-10 pointer-events-none" />
              )}
              <div className="w-full">
                <ScrollArea ref={scrollRef} >
                  <div className="p-4 space-y-2 max-h-[500px]">
                    {clips.map((clip, idx) => (
                      <button
                        key={clip.id}
                        type="button"
                        onClick={() => handleClipSelect(clip.id, idx)}
                        className={cn(
                          "w-full flex items-center gap-3 p-2 rounded-lg text-left transition-all group",
                          selectedIdx === idx
                            ? "bg-zinc-800/80"
                            : "hover:bg-zinc-900"
                        )}
                      >
                        {/* Vertical Thumbnail Placeholder */}
                        <div className="relative w-10 h-16 bg-zinc-800 rounded overflow-hidden flex-shrink-0">
                          <div className="absolute inset-0 flex items-center justify-center">
                            {/* Placeholder visual */}
                            <div className="w-full h-full bg-zinc-700/20"></div>
                          </div>
                        </div>

                        <div className="flex-1 min-w-0">
                          <p className={cn(
                            "text-xs font-medium line-clamp-2 leading-relaxed",
                            selectedIdx === idx ? "text-zinc-100" : "text-foreground group-hover:text-zinc-300"
                          )}>
                            {clip.title || "Como eu uso o Cursor para front-end (do Figma ao código)"}
                          </p>
                        </div>
                      </button>
                    ))}
                    {clips.length === 0 && (
                      <p className="text-xs text-zinc-500 p-2">Nenhum clip gerado ainda.</p>
                    )}
                  </div>
                </ScrollArea>
              </div>
              {showBottomFade && (
                <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-background to-transparent z-10 pointer-events-none" />
              )}
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 overflow-y-auto p-6 md:p-10 lg:ml-80">
            <div className="mb-10 w-full flex justify-end items-center gap-2 max-w-7xl">
              <Button variant="secondary" size="sm" className="h-9 text-zinc-300 hover:bg-zinc-800 hover:text-white gap-2 text-xs">
                <HugeiconsIcon icon={FilterIcon} className="h-4 w-4" />
                <span>Filtrar</span>
              </Button>
              <div className="flex bg-card items-center gap-2  rounded-md px-3 h-9">
                <span className="text-xs text-zinc-300">Selecionar Tudo</span>
                <Checkbox />
              </div>
            </div>
            <div className="max-w-5xl mx-auto space-y-16 pb-20">
              {clips.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-zinc-500">
                  <p>Nenhum clip gerado ainda.</p>
                </div>
              ) : (
                clips.map((clip, idx) => (
                  <div id={`clip-${clip.id}`} key={clip.id} className="flex flex-col lg:flex-row gap-8 items-start group">

                    {/* Left Column: Vertical Video Player */}
                    <div className="shrink-0">
                      <div className="relative w-[280px] aspect-[9/16] bg-card rounded-2xl overflow-hidden border border-zinc-800 shadow-xl">
                        <Checkbox className="absolute top-2 right-2 pointer-events-auto" />
                        <div className="absolute inset-0 flex items-center justify-center text-zinc-700">
                          {/* Placeholder Content */}
                          <HugeiconsIcon icon={PlayIcon} className="h-12 w-12 opacity-50" />
                        </div>
                      </div>
                    </div>

                    {/* Middle Column: Details */}
                    <div className="flex-1 min-w-0 space-y-5 pt-2">
                      {/* Header: ID + Title */}
                      <div>
                        <h3 className="text-lg font-medium text-zinc-100 flex items-start gap-2 leading-tight">
                          <span className="text-primary font-bold">#{idx + 1}</span>
                          {clip.title || "Redimensione vários elementos HTML com Copiar/Colar + IA!"}
                        </h3>
                      </div>

                      {/* Stats & Primary Actions Row */}
                      <div className="flex items-center flex-wrap gap-2">
                        <div className="flex items-baseline gap-1">
                          <span className="text-4xl font-bold text-white tracking-tighter">9.8</span>
                          <span className="text-sm font-medium text-zinc-500">/10</span>
                        </div>

                        <div className="h-8 w-[1px] bg-muted mx-2 hidden sm:block"></div>

                        <Button
                          type="button"
                          className="bg-primary text-white rounded-lg px-6 h-9 text-xs font-medium"
                          onClick={() => setPublishOpen(true)}
                        >
                          <HugeiconsIcon icon={SentIcon} size={16} className="mr-2" />
                          Publicar
                        </Button>

                        <Button variant="secondary" size="icon" className="h-9 w-9 rounded-lg bg-card text-foreground hover:text-white hover:bg-zinc-700">
                          <HugeiconsIcon icon={Download01Icon} size={16} />
                        </Button>
                        <Button variant="secondary" size="icon" className="h-9 w-9 rounded-lg bg-card text-foreground hover:text-white hover:bg-zinc-700" onClick={() => setDialogOpen(true)}>
                          <HugeiconsIcon icon={Share03Icon} size={16} />
                        </Button>
                        <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Compartilhe esse Projeto</DialogTitle>
                              <DialogDescription>
                                Anyone with the link can view
                              </DialogDescription>
                            </DialogHeader>
                            <div className="mt-4 w-full flex gap-2 justify-between items-center">
                              <Select value={value} onValueChange={(v) => setValue(v as "public" | "private")}>
                                <SelectTrigger className="flex items-center gap-2 w-full">
                                  {value === "public" ? (
                                    <div className="flex items-center justi fy-start gap-2">
                                      <HugeiconsIcon icon={GlobeIcon} size={16} />
                                      <span>Qualquer pessoa pode ver</span>
                                    </div>
                                  ) : (
                                    <div className="flex items-center justify-start gap-2">
                                      <HugeiconsIcon icon={LockIcon} size={16} />
                                      <span>Somente você</span>
                                    </div>
                                  )}
                                </SelectTrigger>

                                <SelectContent>
                                  <SelectItem value="public">Qualquer pessoa pode ver</SelectItem>
                                  <SelectItem value="private">Somente você</SelectItem>
                                </SelectContent>
                              </Select>
                              <Button variant="secondary" className="ml-2 bg-foreground hover:bg-foreground/90 text-background">Copy Link</Button>
                            </div>
                            <div className="mt-4 flex items-center">
                              <Input type="email" placeholder="Enter email" className="flex-1" />
                              <Button variant="default" className="ml-2">Invite</Button>
                            </div>
                            <Separator />
                            <div className="mt-4  pt-4 flex items-center justify-between">
                              <Avatar className="h-8 w-8">
                                <AvatarImage src="https://avatars.githubusercontent.com/u/142619236?v=4" alt="account" />
                                <AvatarFallback>SK</AvatarFallback>
                              </Avatar>
                              <div className="ml-3 flex-1">
                                <p className="text-sm font-medium">Rodrigo Carvalho</p>
                                <p className="text-xs text-muted-foreground">rodrigoa0987@gmail.com</p>
                              </div>
                              <span className="text-xs text-muted-foreground">Owner</span>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>

                      {/* Transcript Text */}
                      <div className="bg-transparent">
                        <p className="text-sm text-muted-foreground leading-7">
                          E aí, olha só, com o React Grab, teoricamente agora eu posso vir na minha aplicação, apertar Command C, ele vai abrir isso aqui, para eu selecionar o elemento que eu quero modificar, digamos assim, e aí eu posso falar para ele, por exemplo, esse texto aqui está muito negrito, então eu clico no texto e falo, vou criar um novo agente aqui, esse texto está negrito, diminua ele para a fonte Medium, por exemplo, do Tape. E eu dou um Enter no elemento selecionado ali, e o cursor vai entender automaticamente aonde é que está esse elemento. Olha só, ele entendeu automaticamente, sendo que eu só falei esse texto, eu não falei exatamente qual, por causa que eu copiei, exatamente ele copia qual que é o elemento...
                        </p>
                      </div>
                    </div>

                    {/* Right Column: Floating Actions */}
                    <div className="flex flex-row lg:flex-col gap-3 shrink-0 lg:pt-2 w-full lg:w-auto overflow-x-auto lg:overflow-visible">
                      <ActionButton icon={<HugeiconsIcon icon={Edit02Icon} size={16} />} label="Rename" variant="default" />
                      <ActionButton icon={<HugeiconsIcon icon={Copy01Icon} size={16} />} label="Duplicate" variant="default" />
                      <ActionButton icon={<HugeiconsIcon icon={Delete02Icon} size={16} />} label="Delete" variant="danger" />
                      <ActionButton icon={<HugeiconsIcon icon={ScissorIcon} size={16} />} label="Cut" variant="default" />
                    </div>

                  </div>
                ))
              )}
            </div>

            <Sheet open={publishOpen} onOpenChange={setPublishOpen}>
              <SheetContent
                side="right"
                className="sm:min-w-3xl w-full gap-0 p-0"
                showCloseButton={false}
              >
                <div className="grid grid-cols-1 sm:grid-cols-[240px_1fr] min-h-full">
                  <div className="border-b sm:border-b-0  border-border p-4">
                    <SheetHeader className="p-0">
                      <SheetTitle>Publicar no social</SheetTitle>
                      <SheetDescription className="sr-only">Publicar clip</SheetDescription>
                    </SheetHeader>

                    <div className="mt-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <Checkbox />
                        <div className="relative">
                          <Avatar className="h-8 w-8">
                            <AvatarImage src="https://avatars.githubusercontent.com/u/142619236?v=4" alt="account" />
                            <AvatarFallback>SK</AvatarFallback>
                          </Avatar>
                          <img src="/social/tiktok.svg" alt="TikTok" className="absolute bottom-0 right-0 h-4 w-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-medium truncate">skrodrigo</div>
                          <div className="text-xs text-muted-foreground truncate">@skrodrigo</div>
                        </div>
                      </div>

                      <Button variant="secondary" className="w-full justify-center" size="sm">
                        Manage Accounts
                      </Button>
                    </div>
                  </div>

                  <div className="p-4 space-y-6 bg-card my-6 rounded-l-lg">
                    <div className="space-y-2">
                      <div className="text-sm font-medium">Descrição</div>
                      <Textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="#Frontend #Desenvolvimento #AIEnhancement #Programacao #React
"
                        className="min-h-28"
                      />
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium">Visibilidade</div>
                      <Tabs value={visibility} onValueChange={(v) => {
                        if (v === "public" || v === "private" || v === "friends") setVisibility(v)
                      }} className="w-full">
                        <TabsList className='w-full h-10'>
                          <TabsTrigger value="public" className="flex-1 justify-center">Public</TabsTrigger>
                          <TabsTrigger value="private" className="flex-1 justify-center">Private</TabsTrigger>
                          <TabsTrigger value="friends" className="flex-1 justify-center">Friends</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium">Allow</div>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 text-sm">
                          <Checkbox checked={allowComments} onCheckedChange={(v) => setAllowComments(Boolean(v))} />
                          comentários
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <Checkbox checked={allowDuets} onCheckedChange={(v) => setAllowDuets(Boolean(v))} />
                          Duets
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <Checkbox checked={allowStitch} onCheckedChange={(v) => setAllowStitch(Boolean(v))} />
                          Stitch
                        </label>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm font-medium">Thumbnail</div>
                      <div className="flex items-center gap-3">
                        <div className="h-14 w-10 rounded-md border border-border bg-card flex items-center justify-center">
                          <HugeiconsIcon icon={Upload04Icon} size={16} />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <SheetFooter className="border-t border-border">
                  <div className="flex flex-col sm:flex-row gap-2 sm:items-center justify-between w-full">
                    <Button variant="secondary" onClick={() => setPublishOpen(false)} className="order-last sm:order-first">
                      Cancelar
                    </Button>
                    <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
                      <Input type="datetime-local" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)} className="h-9" />
                      <Button variant="secondary">Agendar</Button>
                      <Button className="bg-primary text-white" onClick={() => setPublishOpen(false)}>
                        Publicar
                      </Button>
                    </div>
                  </div>
                </SheetFooter>
              </SheetContent>
            </Sheet>
          </main>
        </div>
      )}
    </div>
  )
}

function ActionButton({ icon, label, variant = "default" }: { icon: React.ReactNode, label: string, variant?: "default" | "danger" }) {
  return (
    <Button
      variant={variant === "danger" ? "destructive" : "secondary"}
      className="justify-start gap-3 w-full lg:w-32"
    >
      {icon}
      <span>{label}</span>
    </Button>
  )
}