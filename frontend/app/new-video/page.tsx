"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { PageHeader } from "@/components/page-header";
import { Loader2, RefreshCw, VideoOff } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
import { useSearchParams } from "next/navigation";
import { fetchVideos, VideoMetadata } from "@/utils/gallery-utils";
import { VideoCard } from "@/components/VideoCard";
import { VideoOverlay } from "@/components/VideoOverlay";
import { useVideoQueue, registerGalleryRefreshCallback, unregisterGalleryRefreshCallback, VideoQueueItem } from "@/context/video-queue-context";
import { protectImagePrompt, fetchFolders, MediaType } from "@/services/api";
import { useImageSettings } from "@/context/image-settings-context";
import { SlideTransition } from "@/components/ui/page-transition";
import { VideoDetailView } from "@/components/VideoDetailView";
import { VideoQueueSidebar } from "@/components/VideoQueueSidebar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Separate component that uses useSearchParams
function NewVideoPageContent() {
  const searchParams = useSearchParams();
  const folderParam = searchParams.get('folder');
  
  const [videos, setVideos] = useState<VideoMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [autoPlay, setAutoPlay] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [lastRefreshedText, setLastRefreshedText] = useState<string>("Never refreshed");
  const [lastCompletedJobId, setLastCompletedJobId] = useState<string | null>(null);
  const limit = 50;
  
  // Add state for folder selection and video generation
  const [folders, setFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>(folderParam || "root");
  const [isGenerating, setIsGenerating] = useState(false);
  const [remixVideoId, setRemixVideoId] = useState<string>("");
  const [fullscreenVideo, setFullscreenVideo] = useState<VideoMetadata | null>(null);
  
  // Get video generation context
  const { addToQueue, queueItems } = useVideoQueue();
  const imageSettings = useImageSettings();
  
  // Load folders when component mounts
  useEffect(() => {
    const loadFoldersList = async () => {
      try {
        const result = await fetchFolders(MediaType.VIDEO);
        setFolders(result.folders);
      } catch (error) {
        console.error("Error loading folders:", error);
      }
    };
    
    loadFoldersList();
  }, []);
  
  // Handle folder selection change and load videos when folder changes
  useEffect(() => {
    // Set the selected folder and load videos whenever the folder parameter changes
    setSelectedFolder(folderParam || "root");
    setLoading(true); // Show loading state
    
    // Small delay to ensure any navigation transitions complete first
    const loadTimer = setTimeout(() => {
      // Use fetchVideos directly to avoid dependency on loadVideos
      fetchVideos(limit, 0, folderParam || undefined)
        .then((fetchedVideos) => {
          setVideos(fetchedVideos);
          const now = new Date();
          setLastRefreshed(now);
          setLastRefreshedText(`Last refreshed ${formatDistanceToNow(now, { addSuffix: true })}`);
          setHasMore(fetchedVideos.length >= limit);
          setOffset(0);
        })
        .catch((error) => {
          console.error("Failed to load videos:", error);
          toast.error("Error loading videos", {
            description: "Failed to load videos from the gallery"
          });
        })
        .finally(() => {
          setLoading(false);
        });
    }, 50);
    
    return () => clearTimeout(loadTimer);
  }, [folderParam, limit]); // Correctly list dependencies

  const loadVideos = useCallback(async (resetVideos = true, isAutoRefresh = false) => {
    // If we're already in a loading state (e.g., from folder change), don't set it again
    if (resetVideos) {
      if (!isAutoRefresh && !loading) {
        setLoading(true);
      } else if (isAutoRefresh) {
        setIsRefreshing(true);
      }
      setOffset(0);
    } else {
      setIsLoadingMore(true);
    }

    try {
      const fetchedVideos = await fetchVideos(limit, resetVideos ? 0 : offset, folderParam || undefined);
      
      if (resetVideos) {
        // Compare with previous videos to see if we have new content
        const hasNewVideos = fetchedVideos.some(newVideo => 
          !videos.some(existingVideo => existingVideo.id === newVideo.id)
        );
        
        const previousCount = videos.length;
        setVideos(fetchedVideos);
        
        // Update last refreshed time
        const now = new Date();
        setLastRefreshed(now);
        setLastRefreshedText(`Last refreshed ${formatDistanceToNow(now, { addSuffix: true })}`);
        
        // Show feedback about new videos if any were found and it's not an auto-refresh
        if (hasNewVideos && !isAutoRefresh && previousCount > 0 && fetchedVideos.length > previousCount) {
          const newCount = fetchedVideos.length - previousCount;
          toast.success(`${newCount} new video${newCount !== 1 ? 's' : ''} found`, {
            description: "New content has been added to your gallery"
          });
        } else if (!isAutoRefresh && fetchedVideos.length === 0 && previousCount > 0) {
          // If videos were deleted or filtered out
          toast.info("No videos in this view", {
            description: folderParam ? "This folder is currently empty" : "No videos found in the gallery"
          });
        }
      } else {
        const prevCount = videos.length;
        setVideos(prevVideos => [...prevVideos, ...fetchedVideos]);
        
        // Show toast for added videos when loading more
        if (fetchedVideos.length > 0) {
          toast.info(`Loaded ${fetchedVideos.length} more video${fetchedVideos.length !== 1 ? 's' : ''}`, {
            description: `Now showing ${prevCount + fetchedVideos.length} videos in total`,
            duration: 3000
          });
        }
      }
      
      // If we got fewer videos than the limit, there are no more videos to load
      setHasMore(fetchedVideos.length >= limit);
      
      // Update offset for next page
      if (!resetVideos) {
        setOffset(prevOffset => prevOffset + limit);
      }
    } catch (error) {
      console.error("Failed to load videos:", error);
      toast.error("Error loading videos", {
        description: "Failed to load videos from the gallery"
      });
    } finally {
      setLoading(false);
      setIsLoadingMore(false);
      setIsRefreshing(false);
    }
  }, [limit, offset, folderParam, videos, loading]);

  // Register for upload completion notifications
  useEffect(() => {
    // Create a callback function to refresh the gallery
    const refreshGalleryCallback = () => {
      // Check if we're already loading to avoid duplicate refreshes
      if (!loading && !isRefreshing) {
        loadVideos(true, true);
      }
    };
    
    // Register the callback when the component mounts
    registerGalleryRefreshCallback(refreshGalleryCallback);
    
    // Unregister the callback when the component unmounts
    return () => {
      unregisterGalleryRefreshCallback(refreshGalleryCallback);
    };
  }, [loading, isRefreshing, loadVideos]);

  // Toggle auto-refresh
  // Handle auto refresh toggle
  useEffect(() => {
    if (autoRefresh) {
      // Set up a refresh interval (every 30 seconds)
      // Use a function reference that won't change between renders
      const refreshFn = () => {
        if (!isRefreshing && !loading) {
          setIsRefreshing(true);
          // Use a promise to handle the async operation
          fetchVideos(limit, 0, folderParam || undefined)
            .then((fetchedVideos) => {
              setVideos(fetchedVideos);
              const now = new Date();
              setLastRefreshed(now);
              setLastRefreshedText(`Last refreshed ${formatDistanceToNow(now, { addSuffix: true })}`);
              setHasMore(fetchedVideos.length >= limit);
            })
            .catch((error) => {
              console.error("Failed to auto-refresh videos:", error);
            })
            .finally(() => {
              setIsRefreshing(false);
            });
        }
      };
      
      const interval = setInterval(refreshFn, 30000); // 30 seconds
      
      setRefreshInterval(interval);
      
      // Cleanup interval on component unmount or when autoRefresh is turned off
      return () => {
        if (interval) clearInterval(interval);
      };
    } else if (refreshInterval) {
      // Clear the interval if auto refresh is turned off
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, limit, folderParam, isRefreshing, loading, refreshInterval]);

  // Update the "time ago" text every minute
  useEffect(() => {
    if (!lastRefreshed) return;
    
    const updateLastRefreshedText = () => {
      if (lastRefreshed) {
        setLastRefreshedText(`Last refreshed ${formatDistanceToNow(lastRefreshed, { addSuffix: true })}`);
      }
    };
    
    // Update immediately
    updateLastRefreshedText();
    
    // Then update every minute
    const interval = setInterval(updateLastRefreshedText, 60000);
    
    return () => clearInterval(interval);
  }, [lastRefreshed]);

  // Track jobs in progress to avoid immediate refreshes
  const [jobsInProgress, setJobsInProgress] = useState<Record<string, boolean>>({});
  
  // Watch for completion of videos that were actively being generated
  useEffect(() => {
    if (!queueItems || queueItems.length === 0) return;
    
    // Check for items that are fully complete (including uploads)
    const uploadedJobs = queueItems.filter(
      item => item.status === "completed" && 
             item.uploadComplete === true && 
             jobsInProgress[item.id] && 
             item.id !== lastCompletedJobId
    );
    
    if (uploadedJobs.length > 0) {
      // Take the most recent completed job
      const latestJob = uploadedJobs[uploadedJobs.length - 1];
      
      // Update tracking
      const updatedJobsInProgress = {...jobsInProgress};
      uploadedJobs.forEach(job => {
        delete updatedJobsInProgress[job.id];
      });
      setJobsInProgress(updatedJobsInProgress);
      
      // Save this job ID to avoid duplicate refreshes
      setLastCompletedJobId(latestJob.id);
      
      // Wait a moment for backend indexing to complete
      setTimeout(() => {
        // Don't refresh unnecessarily if we just refreshed or are loading
        if (!loading && !isRefreshing) {
          // Do a full refresh of the gallery
          loadVideos(true);
          
          // Don't show additional toast here - the video queue context already shows success notification
        }
      }, 1000);
    }
  }, [queueItems, jobsInProgress, loading, isRefreshing, folderParam, loadVideos, lastCompletedJobId]);

  // No need for a separate loading effect - videos are loaded when the folder changes
  // and can be refreshed manually or with auto-refresh
  
  // Function to handle video deletion
  const handleVideoDeleted = (deletedVideoName: string) => {
    // Remove the deleted video from the state using the unique video name (blob name)
    setVideos(prevVideos => prevVideos.filter(video => video.name !== deletedVideoName));
    
    // If we've deleted a video, we might want to load another one to replace it
    if (hasMore && videos.length < limit * 2) {
      loadMoreVideos();
    }
  };

  // Function to load more videos
  const loadMoreVideos = () => {
    if (!hasMore || isLoadingMore) return;
    loadVideos(false);
  };

  // Generate skeleton placeholders for loading state
  // Function to generate sample tags for videos
  const generateTagsForVideo = (video: VideoMetadata): string[] => {
    // First, check if we have real analysis tags
    if (video.analysis?.tags && video.analysis.tags.length > 0) {
      return video.analysis.tags;
    }
    
    // If the video already has tags from other sources, use those
    if (video.tags && video.tags.length > 0) {
      return video.tags;
    }
    
    // Extract tags from metadata if available
    if (video.originalItem?.metadata?.tags) {
      try {
        const tagString = video.originalItem.metadata.tags;
        if (typeof tagString === 'string') {
          return JSON.parse(tagString);
        }
      } catch (e) {
        console.warn("Failed to parse tags from metadata", e);
      }
    }
    
    // If no real tags are available, return empty array instead of dummy tags
    return [];
  };

  // Group videos into columns for masonry layout
  // When videos are saved to gallery
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleVideosSaved = () => {
    // Refresh the gallery when videos are saved
    loadVideos(true);
  };

  // Handle video generation
  const handleGenerate = async (settings: {
    prompt: string;
    aspectRatio: string;
    resolution: string;
    duration: string;
    variants: string;
    modality: string;
    analyzeVideo: boolean;
    brandsProtection: string;
    imageModel: string;
    hd: boolean;
    vivid: boolean;
    imageSize: string;
    brandProtectionModel: string;
    moderationThresholds: {
      hate: string;
      selfHarm: string;
      sexual: string;
      violence: string;
    };
    saveImages: boolean;
    imageCache: boolean;
    folder?: string;
    brandsList?: string[];
    // NEW: Image-to-Video
    sourceImages?: File[];
    hasSourceImages?: boolean;
  }) => {
    // Skip if already generating
    if (isGenerating) return;
    
    setIsGenerating(true);
    
    // Show immediate feedback to the user
    const toastId = toast.loading(`Creating ${settings.variants} video${parseInt(settings.variants) > 1 ? 's' : ''}...`, {
      description: `${settings.aspectRatio}, ${settings.duration} duration - this may take 1-2 minutes`
    });
    
    try {
      let generationPrompt = settings.prompt;
      
      // Apply brand protection if enabled from global settings
      if (imageSettings.settings.brandsProtection !== "off" && imageSettings.settings.brandsList.length > 0) {
        try {
          // Call the brand protection API
          generationPrompt = await protectImagePrompt(
            settings.prompt,
            imageSettings.settings.brandsList,
            imageSettings.settings.brandsProtection
          );
          
          // Brand protection was applied if prompt changed
        } catch (error) {
          console.error('Error applying brand protection:', error);
          // Don't show a separate error toast for brand protection - just log and continue
          // The main generation will still proceed with the original prompt
          generationPrompt = settings.prompt;
        }
      }
      
      {
        // For real video generation
        try {
          // Convert string values to numbers for type compatibility
          const videoSettings = {
            resolution: settings.resolution,
            duration: parseInt(settings.duration.replace('s', ''), 10), // Convert "5s" to 5
            variants: parseInt(settings.variants, 10),
            aspectRatio: settings.aspectRatio,
            fps: undefined, // Optional
            brandsProtection: settings.brandsProtection,
            brandsList: settings.brandsList,
            analyzeVideo: settings.analyzeVideo, // Pass the analysis setting
            folder: settings.folder, // Pass the folder setting
            // NEW: Pass source images through to the queue context
            sourceImages: settings.sourceImages,
            // NEW: Pass remix video ID if set
            remixVideoId: remixVideoId || undefined
          };
          
          // Add to queue - this will create the job in the backend
          const jobId = await addToQueue(generationPrompt, videoSettings);
          
          // Clear remix ID after successful generation
          if (remixVideoId) {
            setRemixVideoId("");
            toast.success("Video remix started!", {
              description: `Job ID: ${jobId}`
            });
          }
          
          // Track this job to handle its completion properly
          setJobsInProgress(prev => ({
            ...prev,
            [jobId]: true
          }));
          
          // Dismiss the loading toast - the job is now in progress
          toast.dismiss(toastId);
          
          // No need to reset lastCompletedJobId now that we're tracking in jobsInProgress
          
          // Reset generating state
          setIsGenerating(false);
        } catch (error) {
          console.error("Error starting video generation:", error);
          toast.error("Could not connect to the backend API", {
            id: toastId,
            description: "Please try again later"
          });
          setIsGenerating(false);
        }
      }
    } catch (error) {
      console.error("Error during generation:", error);
      setIsGenerating(false);
      toast.error("An error occurred while generating the video", {
        id: toastId,
        description: "Please try again later"
      });
    }
  };
  
  // Handle folder creation
  const handleFolderCreated = (newFolder: string | string[]) => {
    if (Array.isArray(newFolder)) {
      // Update the full folders list
      setFolders(newFolder);
    } else {
      // Single new folder was created
      if (!folders.includes(newFolder)) {
        setFolders(prev => [...prev, newFolder]);
      }
      // Update the selected folder
      setSelectedFolder(newFolder);
    }
  };

  // Function to handle video click - Opens the full-screen modal
  const handleVideoClick = (video: VideoMetadata) => {
    setFullscreenVideo(video);
  };

  // Handle download from sidebar
  const handleSidebarDownload = (item: VideoQueueItem) => {
    if (item.job?.id) {
      const videoId = item.job.id;
      const fileName = `${item.prompt.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_')}_${videoId}.mp4`;
      const downloadUrl = `/api/v1/videos/generations/${videoId}/content?file_name=${encodeURIComponent(fileName)}`;
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success("Download started");
    }
  };

  // Handle remix from sidebar
  const handleSidebarRemix = (item: VideoQueueItem) => {
    if (item.job?.id) {
      setRemixVideoId(item.job.id);
      toast.success("Video ID set for remix", {
        description: "You can now modify the prompt and generate a remix"
      });
    }
  };

  // Handle refresh from sidebar
  const handleSidebarRefresh = () => {
    toast.info("Refreshing status...");
  };

  // Function to handle video deletion from the detail view
  const handleVideoDeletedFromDetail = (videoId: string) => {
    // Remove the deleted video from the state
    setVideos(prevVideos => prevVideos.filter(video => video.id !== videoId));
    
    // Close the detail view
    setFullscreenVideo(null);
    
    // If we've deleted a video, we might want to load another one to replace it
    if (hasMore && videos.length < limit * 2) {
      loadMoreVideos();
    }
  };

  // Function to handle video move from the detail view
  const handleVideoMovedFromDetail = (videoId: string) => {
    // Only remove the moved video if we're in a folder view
    if (folderParam) {
      // Remove the moved video from the current state
      setVideos(prevVideos => prevVideos.filter(video => video.id !== videoId));
      
      // If we've moved a video, we might want to load another one to replace it
      if (hasMore && videos.length < limit * 2) {
        loadMoreVideos();
      }
    } else {
      // When in "All Videos" view, refresh the gallery to update
      loadVideos(true);
    }
    
    // Close the detail view
    setFullscreenVideo(null);
    
    toast.success("Video moved", {
      description: "The video was moved to another folder"
    });
  };



  return (
    <div className="flex h-full w-full">
      {/* Left Sidebar - Video Queue */}
      <VideoQueueSidebar 
        onDownload={handleSidebarDownload}
        onRemix={handleSidebarRemix}
        onRefresh={handleSidebarRefresh}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="px-8 py-6 border-b border-border/50">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold mb-2">Create Your Story</h1>
            <p className="text-muted-foreground">
              Craft engaging video content with AI-powered video generation. Bring your creative vision to life with custom prompts, images, and styles.
            </p>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-8 py-8">
            {/* Remix from Video ID Input */}
            <div className="mb-6">
              <Label htmlFor="remix-video-id" className="text-sm font-medium mb-2 block text-muted-foreground uppercase tracking-wider">
                Remix from Video ID
              </Label>
              <Input
                id="remix-video-id"
                type="text"
                placeholder="video_..."
                value={remixVideoId}
                onChange={(e) => setRemixVideoId(e.target.value)}
                className="max-w-md"
              />
            </div>

            {/* Video Generation Form */}
            <div className="mb-8">
              <VideoOverlay
                folders={folders}
                selectedFolder={selectedFolder}
                onGenerate={handleGenerate}
                onFolderCreated={handleFolderCreated}
                isGenerating={isGenerating}
              />
            </div>

            {/* Generated Videos Gallery - Show below the form */}
            {videos.length > 0 && (
              <div className="mt-12">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-semibold">Recent Videos</h2>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{lastRefreshedText}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadVideos(true, false)}
                      disabled={loading || isRefreshing}
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {videos.slice(0, 12).map((video) => (
                    <VideoCard
                      key={video.id}
                      src={video.src}
                      title={video.title}
                      description={video.description}
                      blobName={video.name}
                      generationId={video.id}
                      prompt={video.originalItem?.metadata?.prompt}
                      duration={video.originalItem?.metadata?.duration ? Number(video.originalItem.metadata.duration) : undefined}
                      resolution={video.originalItem?.metadata?.resolution}
                      onClick={() => handleVideoClick(video)}
                      onDelete={() => handleVideoDeleted(video.name)}
                      tags={generateTagsForVideo(video)}
                      autoPlay={autoPlay}
                    />
                  ))}
                </div>

                {hasMore && videos.length >= 12 && (
                  <div className="flex justify-center mt-8">
                    <Button
                      variant="outline"
                      onClick={loadMoreVideos}
                      disabled={isLoadingMore}
                    >
                      {isLoadingMore ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        "Load More"
                      )}
                    </Button>
                  </div>
                )}
              </div>
            )}

            {videos.length === 0 && !loading && (
              <div className="text-center py-12">
                <VideoOff className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
                <p className="text-muted-foreground">No videos yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Generate your first video using the form above
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Video Detail Modal */}
      <VideoDetailView
        video={fullscreenVideo}
        videos={videos}
        onClose={() => setFullscreenVideo(null)}
        onDelete={handleVideoDeletedFromDetail}
        onMove={handleVideoMovedFromDetail}
        onNavigate={(direction, index) => {
          if (direction === "next" && index < videos.length - 1) {
            setFullscreenVideo(videos[index + 1]);
          } else if (direction === "prev" && index > 0) {
            setFullscreenVideo(videos[index - 1]);
          }
        }}
      />
    </div>
  );
}

export default function NewVideoPage() {
  return (
    <SlideTransition>
      <Suspense fallback={
        <div className="flex flex-col h-full w-full">
          <PageHeader title="Videos" />
          <div className="flex-1 w-full h-full overflow-y-auto">
            <div className="w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 12 }).map((_, index) => (
                  <Card className="overflow-hidden bg-black p-0 border-0 rounded-xl" key={index}>
                    <AspectRatio ratio={16/9} className="bg-muted">
                      <Skeleton className="h-full w-full rounded-none" />
                    </AspectRatio>
                    <div className="p-4 space-y-2">
                      <Skeleton className="h-4 w-2/3" />
                      <Skeleton className="h-3 w-full" />
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      }>
        <NewVideoPageContent />
      </Suspense>
    </SlideTransition>
  );
} 
