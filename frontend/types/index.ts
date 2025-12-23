/**
 * Type definitions for LUMEN frontend
 */

export interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  videoPath?: string
  audioPath?: string
  timestamp: string
}

export interface GenerationRequest {
  prompt: string
  conversation_history?: ConversationMessage[]
  temperature?: number
  reference_audio?: string
  reference_image?: string
}

export interface ConversationMessage {
  role: 'user' | 'model'
  parts: string[]
}

export interface GenerationResponse {
  text: string
  audio_path: string
  audio_url: string
  video_path: string
  video_url: string
  request_id: string
  timestamp: string
  processing_time?: number
}

export interface APIError {
  error: string
  message: string
  request_id?: string
  details?: any
}

export interface HealthCheckResponse {
  status: string
  version: string
  gpu_available: boolean
  gpu_info?: {
    device_name: string
    cuda_version: string
    memory_allocated: string
    memory_reserved: string
  }
  models_path: string
  outputs_path: string
  gemini_configured: boolean
}

export type GenerationStatus = 
  | 'idle' 
  | 'generating-text' 
  | 'generating-audio' 
  | 'generating-video' 
  | 'complete' 
  | 'error'
