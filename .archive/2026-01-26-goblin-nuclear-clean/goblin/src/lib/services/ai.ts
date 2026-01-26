/**
 * AI Service for uDOS Typo Editor
 * 
 * Provides Gemini text and image generation via the uDOS API.
 * - Text generation for markdown content
 * - Image generation via nano-banana model
 * - Markdown image processing
 */

const API_BASE = 'http://localhost:5174';

// Types
export interface GenerationRequest {
  prompt: string;
  type?: 'text' | 'image' | 'sketch';
  model?: string;
  maxTokens?: number;
  temperature?: number;
  context?: string;
}

export interface GenerationResponse {
  success: boolean;
  content?: string;
  text?: string;  // Alias for content (convenience)
  imageUrl?: string;
  imageBase64?: string;
  model?: string;
  tokensUsed?: number;
  costUsd?: number;
  error?: string;
}

export interface ImageProcessRequest {
  markdown: string;
  generateMissing?: boolean;
  style?: 'technical' | 'sketch' | 'diagram' | 'photo';
}

// Gemini text generation
export async function generateText(request: GenerationRequest): Promise<GenerationResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/ai/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: request.prompt,
        provider: 'gemini',
        type: 'text',
        max_tokens: request.maxTokens || 2000,
        temperature: request.temperature || 0.7,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: data.success,
      content: data.content,
      text: data.content,  // Alias
      model: data.model,
      tokensUsed: data.tokens_used,
      costUsd: data.cost_usd,
      error: data.error,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Gemini image generation (nano-banana model)
export async function generateImage(request: GenerationRequest): Promise<GenerationResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/ai/generate/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: request.prompt,
        model: request.model || 'gemini-2.0-flash-exp-image-generation',
        style: 'sketch', // For nano-banana style
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: data.success,
      imageUrl: data.image_url,
      imageBase64: data.image_base64,
      model: data.model,
      error: data.error,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Process markdown to find and generate missing images
export async function processMarkdownImages(request: ImageProcessRequest): Promise<{
  success: boolean;
  markdown: string;
  imagesGenerated: number;
  error?: string;
}> {
  try {
    const response = await fetch(`${API_BASE}/api/ai/process-images`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        markdown: request.markdown,
        generate_missing: request.generateMissing ?? true,
        style: request.style || 'technical',
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: data.success,
      markdown: data.markdown,
      imagesGenerated: data.images_generated || 0,
      error: data.error,
    };
  } catch (error) {
    return {
      success: false,
      markdown: request.markdown,
      imagesGenerated: 0,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Quick action type
export interface QuickAction {
  name: string;
  prompt: string;
  maxTokens: number;
  type: 'text' | 'image';
}

// Quick actions for editor - declarative definitions
export const quickActions: Record<string, QuickAction> = {
  expand: {
    name: 'Expand',
    prompt: 'Expand and elaborate on this text, keeping the same style and format:',
    maxTokens: 1000,
    type: 'text',
  },
  summarize: {
    name: 'Summarize',
    prompt: 'Summarize this text concisely:',
    maxTokens: 500,
    type: 'text',
  },
  improve: {
    name: 'Improve',
    prompt: 'Improve this text - fix grammar, clarity, and flow while keeping the meaning:',
    maxTokens: 1000,
    type: 'text',
  },
  sketch: {
    name: 'Sketch',
    prompt: 'Simple black and white technical sketch. Clean lines, minimal shading, diagram style:',
    maxTokens: 500,
    type: 'image',
  },
  continue: {
    name: 'Continue',
    prompt: 'Continue writing this text naturally:',
    maxTokens: 500,
    type: 'text',
  },
  toChecklist: {
    name: 'To Checklist',
    prompt: 'Convert this into a markdown checklist with - [ ] format:',
    maxTokens: 500,
    type: 'text',
  },
};

// Execute a quick action
export async function executeQuickAction(
  actionName: string,
  text: string
): Promise<GenerationResponse> {
  const action = quickActions[actionName];
  if (!action) {
    return { success: false, error: `Unknown action: ${actionName}` };
  }

  if (action.type === 'image') {
    return generateImage({
      prompt: `${action.prompt} ${text}`,
      type: 'sketch',
    });
  }

  return generateText({
    prompt: `${action.prompt}\n\n${text}`,
    maxTokens: action.maxTokens,
  });
}
