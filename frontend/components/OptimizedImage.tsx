"use client";

import Image from 'next/image';
import { useState, forwardRef } from 'react';
import { isExternalImageUrl, getFallbackImageUrl, type ImageLoadingType, IMAGE_LOADING_CONFIG, isAzureBlobStorageUrl } from '@/utils/image-utils';
import { API_BASE_URL } from '@/services/api';

interface OptimizedImageProps {
  src: string;
  alt: string;
  fill?: boolean;
  sizes?: string;
  className?: string;
  onLoad?: () => void;
  onError?: () => void;
  priority?: boolean;
  width?: number;
  height?: number;
  loadingType?: ImageLoadingType;
  quality?: number;
}

/**
 * Convert Azure Blob Storage URL to backend proxy URL
 * Since managed identity is enabled and public access is disabled,
 * all blob access must go through the backend
 */
function getProxiedImageUrl(url: string): string {
  // If it's already a backend URL, return as-is
  if (url.startsWith(API_BASE_URL)) {
    return url;
  }
  
  // If it's an Azure Blob Storage URL, proxy it through backend
  if (isAzureBlobStorageUrl(url)) {
    // Extract blob name from URL
    // Format: https://<account>.blob.core.windows.net/<container>/<blobname>
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/').filter(p => p);
    if (pathParts.length >= 2) {
      const container = pathParts[0];
      const blobName = pathParts.slice(1).join('/');
      // Route through backend proxy endpoint
      return `${API_BASE_URL}/gallery/${container}/${blobName}`;
    }
  }
  
  return url;
}

// Custom image component that handles external URLs gracefully
export const OptimizedImage = forwardRef<HTMLImageElement, OptimizedImageProps>(
  ({ 
    src, 
    alt, 
    fill, 
    sizes, 
    className, 
    onLoad, 
    onError, 
    priority, 
    width, 
    height, 
    loadingType = 'gallery',
    quality 
  }, ref) => {
    const [imageError, setImageError] = useState(false);
    const [fallbackUsed, setFallbackUsed] = useState(false);
    
    // Get loading configuration
    const loadingConfig = IMAGE_LOADING_CONFIG[loadingType];
    const finalSizes = sizes || loadingConfig.sizes;
    const finalPriority = priority !== undefined ? priority : loadingConfig.priority;
    const finalQuality = quality || loadingConfig.quality;
    
    // Convert Azure Blob URLs to backend proxy URLs
    const proxiedSrc = getProxiedImageUrl(src);
    
    // Check if the image is from an external source
    const isExternal = isExternalImageUrl(proxiedSrc);
    
    // Handle image error
    const handleError = () => {
      if (!fallbackUsed) {
        setImageError(true);
        setFallbackUsed(true);
      }
      onError?.();
    };
    
    // Handle image load
    const handleLoad = () => {
      setImageError(false);
      onLoad?.();
    };
    
    // Use fallback image if there was an error
    const imageSrc = imageError && fallbackUsed 
      ? getFallbackImageUrl(width || 400, height || 300)
      : proxiedSrc;
    
    // Use unoptimized for external URLs (including backend-proxied images)
    if (isExternal) {
      const safeWidth = !fill ? (width || 1024) : undefined;
      const safeHeight = !fill ? (height || 1024) : undefined;
      
      return (
        <Image
          ref={ref}
          src={imageSrc}
          alt={alt}
          fill={fill}
          width={safeWidth}
          height={safeHeight}
          sizes={finalSizes}
          className={className}
          onLoad={handleLoad}
          onError={handleError}
          priority={finalPriority}
          quality={finalQuality}
          unoptimized
        />
      );
    }
    
    // For internal images, use optimized version
    const safeWidth = !fill ? (width || 1024) : undefined;
    const safeHeight = !fill ? (height || 1024) : undefined;
    
    return (
      <Image
        ref={ref}
        src={imageSrc}
        alt={alt}
        fill={fill}
        width={safeWidth}
        height={safeHeight}
        sizes={finalSizes}
        className={className}
        onLoad={handleLoad}
        onError={handleError}
        priority={finalPriority}
        quality={finalQuality}
      />
    );
  }
);

OptimizedImage.displayName = 'OptimizedImage'; 