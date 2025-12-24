import { request } from '../http'
import type { ConfirmUploadResponse, GenerateUploadUrlResponse, IngestFromUrlResponse } from './types/videos-types'

export async function generateUploadUrl(
  filename: string,
  fileSize: number,
  videoId: string,
  contentType: string = 'video/mp4'
): Promise<GenerateUploadUrlResponse> {
  return request<GenerateUploadUrlResponse>('/api/videos/upload/generate-url/', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      file_size: fileSize,
      video_id: videoId,
      content_type: contentType,
    }),
  })
}

export async function uploadToR2(
  uploadUrl: string,
  file: File,
  contentType: string = 'video/mp4'
): Promise<void> {
  try {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Upload error response:', errorText)
      throw new Error(`Erro ao fazer upload do arquivo: ${response.status} ${response.statusText}`)
    }
  } catch (error) {
    console.error('Upload error:', error)
    throw error
  }
}

export async function confirmUpload(
  videoId: string,
  fileSize: number
): Promise<ConfirmUploadResponse> {
  return request<ConfirmUploadResponse>('/api/videos/upload/confirm/', {
    method: 'POST',
    body: JSON.stringify({
      video_id: videoId,
      file_size: fileSize,
    }),
  })
}

export async function ingestVideoFromUrl(
  sourceUrl: string,
  sourceType: string = 'url'
): Promise<IngestFromUrlResponse> {
  return request<IngestFromUrlResponse>('/api/videos/upload/from-url/', {
    method: 'POST',
    body: JSON.stringify({
      source_url: sourceUrl,
      source_type: sourceType,
    }),
  })
}

export interface StartIngestionFromUrlResponse {
  video_id: string
  status: string
  task_id: string
  job_id?: string
}

export async function startIngestionFromUrl(
  videoId: string,
  configuration?: Record<string, any>
): Promise<StartIngestionFromUrlResponse> {
  return request<StartIngestionFromUrlResponse>('/api/videos/upload/from-url/start/', {
    method: 'POST',
    body: JSON.stringify({
      video_id: videoId,
      configuration,
    }),
  })
}

export async function uploadVideo(file: File, videoId: string): Promise<string> {
  try {
    // Step 1: Gerar URL pré-assinada
    const { upload_url } = await generateUploadUrl(
      file.name,
      file.size,
      videoId,
      file.type
    )

    // Step 2: Fazer upload para R2
    await uploadToR2(upload_url, file, file.type)

    // Step 3: Confirmar upload
    await confirmUpload(videoId, file.size)

    return videoId
  } catch (error) {
    throw error
  }
}
