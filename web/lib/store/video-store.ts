import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

interface VideoState {
  videoFile: File | null
  videoUrl: string | null
  videoId: string | null
  videoTitle: string | null
  thumbnailUrl: string | null
  duration: number | null
  fileSize: number | null
  taskId: string | null
  processing: {
    jobId: string | null
    status: string | null
    progress: number
    config: any | null
  }
  setVideoFile: (file: File | null) => void
  setVideoFromUrl: (payload: {
    videoId: string
    title: string
    thumbnailUrl: string | null
    duration: number | null
    fileSize: number | null
    taskId: string | null
    sourceUrl: string
  }) => void
  setVideoDetails: (payload: {
    videoTitle?: string | null
    thumbnailUrl?: string | null
    duration?: number | null
    fileSize?: number | null
  }) => void
  setProcessingConfig: (config: any | null) => void
  setProcessingJobId: (jobId: string | null) => void
  setProcessingStatus: (status: string | null) => void
  setProcessingProgress: (progress: number) => void
  resetProcessing: () => void
  clearVideo: () => void
}

export const useVideoStore = create<VideoState>()(
  persist(
    (set) => ({
      videoFile: null,
      videoUrl: null,
      videoId: null,
      videoTitle: null,
      thumbnailUrl: null,
      duration: null,
      fileSize: null,
      taskId: null,
      processing: {
        jobId: null,
        status: null,
        progress: 0,
        config: null,
      },
      setVideoFile: (file) => {
        set((state) => {
          if (state.videoUrl) {
            URL.revokeObjectURL(state.videoUrl)
          }
          const newUrl = file ? URL.createObjectURL(file) : null
          return {
            videoFile: file,
            videoUrl: newUrl,
            videoId: null,
            videoTitle: file ? file.name : null,
            thumbnailUrl: null,
            duration: null,
            fileSize: file ? file.size : null,
            taskId: null,
          }
        })
      },
      setVideoFromUrl: (payload) =>
        set((state) => {
          if (state.videoUrl) {
            URL.revokeObjectURL(state.videoUrl)
          }
          return {
            videoFile: null,
            videoUrl: payload.sourceUrl,
            videoId: payload.videoId,
            videoTitle: payload.title,
            thumbnailUrl: payload.thumbnailUrl,
            duration: payload.duration,
            fileSize: payload.fileSize,
            taskId: payload.taskId,
          }
        }),
      setVideoDetails: (payload) =>
        set((state) => ({
          videoTitle:
            payload.videoTitle === undefined ? state.videoTitle : payload.videoTitle,
          thumbnailUrl:
            payload.thumbnailUrl === undefined ? state.thumbnailUrl : payload.thumbnailUrl,
          duration: payload.duration === undefined ? state.duration : payload.duration,
          fileSize: payload.fileSize === undefined ? state.fileSize : payload.fileSize,
        })),
      setProcessingConfig: (config) =>
        set((state) => {
          const current = state.processing.config
          const next = config ?? null

          if (current === next) {
            return state
          }

          // Avoid re-updating with equivalent objects (prevents render loops)
          try {
            if (
              current &&
              next &&
              JSON.stringify(current) === JSON.stringify(next)
            ) {
              return state
            }
          } catch {
            // ignore stringify issues; fall through to update
          }

          return {
            processing: {
              ...state.processing,
              config: next,
            },
          }
        }),
      setProcessingJobId: (jobId) =>
        set((state) => ({
          processing: {
            ...state.processing,
            jobId,
          },
        })),
      setProcessingStatus: (status) =>
        set((state) => ({
          processing: {
            ...state.processing,
            status,
          },
        })),
      setProcessingProgress: (progress) =>
        set((state) => ({
          processing: {
            ...state.processing,
            progress,
          },
        })),
      resetProcessing: () =>
        set((state) => ({
          processing: {
            ...state.processing,
            jobId: null,
            status: null,
            progress: 0,
            config: null,
          },
        })),
      clearVideo: () =>
        set((state) => {
          if (state.videoUrl) {
            URL.revokeObjectURL(state.videoUrl)
          }
          return {
            videoFile: null,
            videoUrl: null,
            videoId: null,
            videoTitle: null,
            thumbnailUrl: null,
            duration: null,
            fileSize: null,
            taskId: null,
          }
        }),
    }),
    {
      name: 'klipou-video-store',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        videoId: state.videoId,
        videoTitle: state.videoTitle,
        thumbnailUrl: state.thumbnailUrl,
        duration: state.duration,
        fileSize: state.fileSize,
        taskId: state.taskId,
        processing: state.processing,
      }),
    }
  )
)
