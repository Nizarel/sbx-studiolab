"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Download, Wand2, RefreshCw, Clock, Loader2, X, Copy } from "lucide-react";
import { toast } from "sonner";
import type { VideoQueueItem } from "@/context/video-queue-context";

interface VideoQueueSidebarCardProps {
  item: VideoQueueItem;
  onDownload?: (item: VideoQueueItem) => void;
  onRemix?: (item: VideoQueueItem) => void;
  onRefresh?: (item: VideoQueueItem) => void;
  onRemove?: (id: string) => void;
}

export function VideoQueueSidebarCard({ item, onDownload, onRemix, onRefresh, onRemove }: VideoQueueSidebarCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Get display status
  const getStatusBadge = () => {
    const jobStatus = item.job?.status;
    
    if (jobStatus === "queued") {
      return (
        <Badge variant="secondary" className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
          <Clock className="w-3 h-3 mr-1" />
          QUEUED
        </Badge>
      );
    }
    
    if (jobStatus === "in_progress") {
      return (
        <Badge variant="secondary" className="bg-blue-500/20 text-blue-400 border-blue-500/30">
          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          PROCESSING
        </Badge>
      );
    }
    
    if (jobStatus === "completed") {
      return (
        <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
          READY
        </Badge>
      );
    }
    
    if (jobStatus === "failed") {
      return (
        <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30">
          <X className="w-3 h-3 mr-1" />
          FAILED
        </Badge>
      );
    }
    
    return null;
  };

  // Get progress percentage
  const getProgressPercent = () => {
    if (item.job?.status === "in_progress") {
      return item.progress || 0;
    }
    if (item.job?.status === "completed") {
      return 100;
    }
    return 0;
  };

  // Get display title (generated title from queue item, or first 50 chars of prompt)
  const getTitle = () => {
    // Try to get generated title from queue item first
    if (item.generatedTitle) {
      return item.generatedTitle;
    }
    // Fallback to truncated prompt
    const title = item.prompt.substring(0, 50);
    return title.length < item.prompt.length ? `${title}...` : title;
  };

  // Get metadata display
  const getMetadata = () => {
    const duration = item.job?.metadata?.seconds || "?";
    const size = item.job?.metadata?.size || "?";
    return `${duration}s · sora-2 · ${size}`;
  };

  // Get completion time
  const getCompletionTime = () => {
    if (item.job?.status === "completed" && item.createdAt) {
      const createdDate = item.createdAt instanceof Date ? item.createdAt : new Date(item.createdAt);
      const now = new Date();
      const diffMs = now.getTime() - createdDate.getTime();
      const diffMins = Math.round(diffMs / 60000);
      
      return `Completed ${createdDate.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })} • ${diffMins} min`;
    }
    return null;
  };

  // Copy video ID to clipboard
  const handleCopyId = () => {
    const fullId = item.job?.id || item.id;
    navigator.clipboard.writeText(fullId);
    toast.success("Video ID copied to clipboard");
  };

  const isProcessing = item.job?.status === "in_progress";
  const isCompleted = item.job?.status === "completed";
  const isQueued = item.job?.status === "queued";
  const canDownload = isCompleted && item.uploadComplete;
  const canRemix = isCompleted; // Remix available as soon as completed

  return (
    <Card 
      className="bg-background/50 border-border/50 hover:border-border transition-all mb-3 relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardContent className="p-4">
        {/* Close button */}
        {isHovered && onRemove && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 h-6 w-6 z-10"
            onClick={() => onRemove(item.id)}
          >
            <X className="h-4 w-4" />
          </Button>
        )}

        {/* Title and Status */}
        <div className="flex items-start justify-between mb-2 gap-2">
          <div className="flex-1">
            <h4 className="text-sm font-medium line-clamp-2 mb-1">{getTitle()}</h4>
            {/* Video ID with copy button - shows full ID */}
            <div className="flex items-center gap-1">
              <code className="text-xs text-muted-foreground font-mono truncate max-w-[200px]">
                {item.job?.id || item.id}
              </code>
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 hover:bg-muted/50"
                onClick={handleCopyId}
              >
                <Copy className="h-3 w-3 text-muted-foreground" />
              </Button>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Prompt */}
        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
          {item.prompt}
        </p>

        {/* Metadata */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
          <span>{getMetadata()}</span>
        </div>

        {/* Progress for processing jobs */}
        {isProcessing && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Processing {Math.round(getProgressPercent())}%</span>
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => onRefresh(item)}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Refresh
                </Button>
              )}
            </div>
            <Progress value={getProgressPercent()} className="h-1" />
          </div>
        )}

        {/* Queued status */}
        {isQueued && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Processing...</span>
              </div>
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => onRefresh(item)}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Refresh
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Completion time */}
        {getCompletionTime() && (
          <p className="text-xs text-muted-foreground mb-3">
            {getCompletionTime()}
          </p>
        )}

        {/* Action buttons */}
        {(canDownload || canRemix) && (
          <div className="flex gap-2">
            {canDownload && onDownload && (
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => onDownload(item)}
              >
                <Download className="h-3 w-3 mr-1" />
                Download
              </Button>
            )}
            {canRemix && onRemix && (
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => onRemix(item)}
              >
                <Wand2 className="h-3 w-3 mr-1" />
                Remix
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
