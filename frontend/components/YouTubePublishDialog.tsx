"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Loader2, Youtube, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { publishToYouTube, VideoPrivacyStatus, PublishResponse } from "@/services/api";
import { Badge } from "@/components/ui/badge";

interface YouTubePublishDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  videoBlobName: string;
  videoTitle?: string;
  videoPrompt?: string;
}

const YOUTUBE_CATEGORIES = [
  { id: "1", name: "Film & Animation" },
  { id: "2", name: "Autos & Vehicles" },
  { id: "10", name: "Music" },
  { id: "15", name: "Pets & Animals" },
  { id: "17", name: "Sports" },
  { id: "19", name: "Travel & Events" },
  { id: "20", name: "Gaming" },
  { id: "22", name: "People & Blogs" },
  { id: "23", name: "Comedy" },
  { id: "24", name: "Entertainment" },
  { id: "25", name: "News & Politics" },
  { id: "26", name: "Howto & Style" },
  { id: "27", name: "Education" },
  { id: "28", name: "Science & Technology" },
];

export function YouTubePublishDialog({
  open,
  onOpenChange,
  videoBlobName,
  videoTitle,
  videoPrompt,
}: YouTubePublishDialogProps) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null);
  
  // Form state
  const [title, setTitle] = useState(videoTitle || "");
  const [description, setDescription] = useState(videoPrompt || "");
  const [tags, setTags] = useState("ai-generated, sora");
  const [categoryId, setCategoryId] = useState("22"); // People & Blogs
  const [privacyStatus, setPrivacyStatus] = useState<VideoPrivacyStatus>(VideoPrivacyStatus.UNLISTED);
  const [madeForKids, setMadeForKids] = useState(false);

  const handlePublish = async () => {
    if (!title.trim()) {
      toast.error("Title is required", {
        description: "Please enter a title for your video"
      });
      return;
    }

    setIsPublishing(true);
    setPublishedUrl(null);

    try {
      const tagArray = tags.split(",").map(tag => tag.trim()).filter(tag => tag.length > 0);
      
      const result: PublishResponse = await publishToYouTube({
        video_blob_name: videoBlobName,
        title: title.trim(),
        description: description.trim(),
        tags: tagArray,
        category_id: categoryId,
        privacy_status: privacyStatus,
        made_for_kids: madeForKids,
      });

      if (result.success && result.video_url) {
        setPublishedUrl(result.video_url);
        toast.success("Video published to YouTube!", {
          description: `Your video is now live on YouTube`,
          action: {
            label: "View on YouTube",
            onClick: () => window.open(result.video_url, '_blank'),
          },
        });
      } else {
        throw new Error(result.message || "Failed to publish video");
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred";
      toast.error("Failed to publish to YouTube", {
        description: errorMessage
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleClose = () => {
    if (!isPublishing) {
      setPublishedUrl(null);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-500" />
            Publish to YouTube
          </DialogTitle>
          <DialogDescription>
            Publish your AI-generated video directly to your YouTube channel
          </DialogDescription>
        </DialogHeader>

        {publishedUrl ? (
          // Success state
          <div className="py-6 space-y-4">
            <div className="text-center space-y-2">
              <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                <Youtube className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold">Video Published Successfully!</h3>
              <p className="text-sm text-muted-foreground">
                Your video is now live on YouTube
              </p>
            </div>
            
            <div className="flex justify-center">
              <Button
                onClick={() => window.open(publishedUrl, '_blank')}
                className="gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View on YouTube
              </Button>
            </div>
          </div>
        ) : (
          // Form state
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                placeholder="Enter video title (max 100 characters)"
                value={title}
                onChange={(e) => setTitle(e.target.value.slice(0, 100))}
                maxLength={100}
                disabled={isPublishing}
              />
              <p className="text-xs text-muted-foreground">
                {title.length}/100 characters
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter video description (max 5000 characters)"
                value={description}
                onChange={(e) => setDescription(e.target.value.slice(0, 5000))}
                maxLength={5000}
                rows={4}
                disabled={isPublishing}
              />
              <p className="text-xs text-muted-foreground">
                {description.length}/5000 characters
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <Input
                id="tags"
                placeholder="Enter tags separated by commas"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                disabled={isPublishing}
              />
              <p className="text-xs text-muted-foreground">
                Separate tags with commas (e.g., "ai, video, sora")
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select value={categoryId} onValueChange={setCategoryId} disabled={isPublishing}>
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {YOUTUBE_CATEGORIES.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="privacy">Privacy</Label>
                <Select 
                  value={privacyStatus} 
                  onValueChange={(value) => setPrivacyStatus(value as VideoPrivacyStatus)}
                  disabled={isPublishing}
                >
                  <SelectTrigger id="privacy">
                    <SelectValue placeholder="Select privacy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={VideoPrivacyStatus.PUBLIC}>
                      Public
                    </SelectItem>
                    <SelectItem value={VideoPrivacyStatus.UNLISTED}>
                      Unlisted
                    </SelectItem>
                    <SelectItem value={VideoPrivacyStatus.PRIVATE}>
                      Private
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <Label htmlFor="made-for-kids" className="text-sm font-medium">
                  Made for kids
                </Label>
                <p className="text-xs text-muted-foreground">
                  Is this video directed to children?
                </p>
              </div>
              <Switch
                id="made-for-kids"
                checked={madeForKids}
                onCheckedChange={setMadeForKids}
                disabled={isPublishing}
              />
            </div>

            <div className="rounded-lg bg-muted p-3 space-y-1">
              <p className="text-xs font-medium">Note:</p>
              <p className="text-xs text-muted-foreground">
                You'll need to authorize this app with your YouTube account on first use. 
                The video will be uploaded from Azure Blob Storage to your YouTube channel.
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          {!publishedUrl && (
            <>
              <Button
                variant="outline"
                onClick={handleClose}
                disabled={isPublishing}
              >
                Cancel
              </Button>
              <Button
                onClick={handlePublish}
                disabled={isPublishing || !title.trim()}
              >
                {isPublishing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <Youtube className="h-4 w-4 mr-2" />
                    Publish to YouTube
                  </>
                )}
              </Button>
            </>
          )}
          {publishedUrl && (
            <Button onClick={handleClose}>
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
