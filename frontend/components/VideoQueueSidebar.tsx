"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Download, Library } from "lucide-react";
import { VideoQueueSidebarCard } from "./VideoQueueSidebarCard";
import { useVideoQueue, VideoQueueItem } from "@/context/video-queue-context";

interface VideoQueueSidebarProps {
  onDownload?: (item: VideoQueueItem) => void;
  onRemix?: (item: VideoQueueItem) => void;
  onRefresh?: (item: VideoQueueItem) => void;
  onDownloadAll?: () => void;
}

export function VideoQueueSidebar({ onDownload, onRemix, onRefresh, onDownloadAll }: VideoQueueSidebarProps) {
  const { queueItems, removeFromQueue } = useVideoQueue();

  // Filter to show only recent generations (not older than 1 hour)
  const recentItems = queueItems.filter(item => {
    const createdDate = item.createdAt instanceof Date ? item.createdAt : new Date(item.createdAt);
    const ageMs = Date.now() - createdDate.getTime();
    const ageHours = ageMs / (1000 * 60 * 60);
    return ageHours < 1; // Only show items from last hour
  });

  const hasItems = recentItems.length > 0;
  const hasCompletedItems = recentItems.some(item => item.job?.status === "completed");

  return (
    <div className="w-96 border-r border-border/50 bg-background/30 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border/50 flex-shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <Library className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Library</span>
        </div>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Your generations</h2>
          {hasCompletedItems && onDownloadAll && (
            <Button variant="ghost" size="sm" onClick={onDownloadAll}>
              <Download className="h-3 w-3 mr-1" />
              Download all
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Downloads may expire after one hour.
        </p>
      </div>

      {/* Scrollable content */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {hasItems ? (
            recentItems.map((item) => (
              <VideoQueueSidebarCard
                key={item.id}
                item={item}
                onDownload={onDownload}
                onRemix={onRemix}
                onRefresh={onRefresh}
                onRemove={removeFromQueue}
              />
            ))
          ) : (
            <div className="text-center py-12">
              <Library className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <p className="text-sm text-muted-foreground">No generations yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Your generated videos will appear here
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
