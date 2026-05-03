import axios from "axios";
import {
  ResultsData,
  SDGClassificationRequest,
  SDGClassificationResponse,
  CacheMeta,
} from "@/types/main";

const API_BASE_URL = "http://127.0.0.1:5000/";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Cache metadata store (per request)
let lastCacheMeta: CacheMeta | null = null;

export const getLastCacheMeta = (): CacheMeta | null => lastCacheMeta;

export const clearCacheMeta = (): void => {
  lastCacheMeta = null;
};

// Helper to extract cache headers from response
const extractCacheMeta = (response: any): CacheMeta | null => {
  const cacheHeader = response.headers['x-cache'];
  if (!cacheHeader) return null;

  return {
    cached: cacheHeader === 'HIT',
    cacheStatus: cacheHeader as 'HIT' | 'MISS',
    cacheAge: parseInt(response.headers['x-cache-age'] || '0'),
  };
};

export const sdgApi = {
  classifyAurora: async (
    data: SDGClassificationRequest,
  ): Promise<SDGClassificationResponse> => {
    const response = await apiClient.post<SDGClassificationResponse>(
      "api/classify_aurora",
      data,
    );
    lastCacheMeta = extractCacheMeta(response);
    return response.data;
  },

  classifySTDescription: async (
    data: SDGClassificationRequest,
  ): Promise<SDGClassificationResponse> => {
    const response = await apiClient.post<SDGClassificationResponse>(
      "api/classify_st_description",
      data,
    );
    lastCacheMeta = extractCacheMeta(response);
    return response.data;
  },

  classifySTUrl: async (
    data: SDGClassificationRequest,
  ): Promise<SDGClassificationResponse> => {
    const response = await apiClient.post<SDGClassificationResponse>(
      "api/classify_st_url",
      data,
    );
    lastCacheMeta = extractCacheMeta(response);
    return response.data;
  },

  // Cache management endpoints
  getCacheStats: async (): Promise<any> => {
    const response = await apiClient.get("api/cache/stats");
    return response.data;
  },

  clearCache: async (): Promise<any> => {
    const response = await apiClient.post("api/cache/clear");
    return response.data;
  },
};

// Helper to get classification by model

export const classifyByModel = async (
  modelType: "aurora" | "st-description" | "st-url",
  data: SDGClassificationRequest,
): Promise<SDGClassificationResponse> => {
  let response: SDGClassificationResponse;
  
  switch (modelType) {
    case "aurora":
      response = await sdgApi.classifyAurora(data);
      break;
    case "st-description":
      response = await sdgApi.classifySTDescription(data);
      break;
    case "st-url":
      response = await sdgApi.classifySTUrl(data);
      break;
    default:
      response = await sdgApi.classifyAurora(data);
  }
  
  // Attach cache meta to response for UI display
  const cacheMeta = getLastCacheMeta();
  if (cacheMeta) {
    (response as any)._cacheMeta = cacheMeta;
  }
  
  return response;
};
