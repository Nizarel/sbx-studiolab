"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Wand2 } from "lucide-react";
import { createRemixVideoJob } from "@/services/api";
import { toast } from "sonner";

interface VideoRemixDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  videoId: string;
  originalPrompt?: string;
  currentSize?: string;
  currentDuration?: number;
}

const SORA2_RESOLUTIONS = [
  { value: "1280x720", label: "1280x720 (Landscape)" },
  { value: "720x1280", label: "720x1280 (Portrait)" },
  { value: "1792x1024", label: "1792x1024 (Wide)" },
  { value: "1024x1792", label: "1024x1792 (Tall)" },
];

const SORA2_DURATIONS = [
  { value: "4", label: "4 seconds" },
  { value: "8", label: "8 seconds" },
  { value: "12", label: "12 seconds" },
];

export function VideoRemixDialog({
  open,
  onOpenChange,
  videoId,
  originalPrompt = "",
  currentSize = "1280x720",
  currentDuration = 10,
}: VideoRemixDialogProps) {
  const [prompt, setPrompt] = useState("");
  const [size, setSize] = useState(currentSize);
  const [seconds, setSeconds] = useState(
    currentDuration === 4 || currentDuration === 8 || currentDuration === 12
      ? currentDuration.toString()
      : "8"
  );
  const [nVariants, setNVariants] = useState("1");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      toast.error("Prompt required", {
        description: "Please describe the changes you want to make to the video",
      });
      return;
    }

    try {
      setIsSubmitting(true);

      const response = await createRemixVideoJob({
        remix_video_id: videoId,
        prompt: prompt.trim(),
        seconds: parseInt(seconds),
        size: size,
        n_variants: parseInt(nVariants),
      });

      toast.success("Remix job created", {
        description: `Your video remix has been queued. Job ID: ${response.job.id}`,
      });

      // Close dialog and reset form
      onOpenChange(false);
      setPrompt("");
      setSize(currentSize);
      setSeconds(
        currentDuration === 4 || currentDuration === 8 || currentDuration === 12
          ? currentDuration.toString()
          : "8"
      );
      setNVariants("1");
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "An unknown error occurred";
      toast.error("Failed to create remix", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5" />
            Remix Video
          </DialogTitle>
          <DialogDescription>
            Create a new version of this video with targeted edits. Describe the
            changes you want to make.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Original prompt reference */}
          {originalPrompt && (
            <div className="grid gap-2">
              <Label className="text-sm text-muted-foreground">
                Original prompt
              </Label>
              <p className="text-sm bg-muted p-3 rounded-md">
                {originalPrompt}
              </p>
            </div>
          )}

          {/* Remix prompt */}
          <div className="grid gap-2">
            <Label htmlFor="remix-prompt">
              Remix prompt <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="remix-prompt"
              placeholder="Describe the changes you want to make (e.g., 'Change the time to sunset', 'Add rain', 'Make it black and white')"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Resolution */}
          <div className="grid gap-2">
            <Label htmlFor="resolution">Resolution</Label>
            <Select value={size} onValueChange={setSize}>
              <SelectTrigger id="resolution">
                <SelectValue placeholder="Select resolution" />
              </SelectTrigger>
              <SelectContent>
                {SORA2_RESOLUTIONS.map((res) => (
                  <SelectItem key={res.value} value={res.value}>
                    {res.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Duration */}
          <div className="grid gap-2">
            <Label htmlFor="duration">Duration</Label>
            <Select value={seconds} onValueChange={setSeconds}>
              <SelectTrigger id="duration">
                <SelectValue placeholder="Select duration" />
              </SelectTrigger>
              <SelectContent>
                {SORA2_DURATIONS.map((dur) => (
                  <SelectItem key={dur.value} value={dur.value}>
                    {dur.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Number of variants */}
          <div className="grid gap-2">
            <Label htmlFor="variants">Number of variants</Label>
            <Select value={nVariants} onValueChange={setNVariants}>
              <SelectTrigger id="variants">
                <SelectValue placeholder="Select variants" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 variant</SelectItem>
                <SelectItem value="2">2 variants</SelectItem>
                <SelectItem value="3">3 variants</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating remix...
              </>
            ) : (
              <>
                <Wand2 className="mr-2 h-4 w-4" />
                Create remix
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
