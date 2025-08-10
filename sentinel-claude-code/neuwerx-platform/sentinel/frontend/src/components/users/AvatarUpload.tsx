'use client';

import { useState, useRef } from 'react';
import { Camera, Upload, X, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';

interface AvatarUploadProps {
  userId: string;
  currentAvatarUrl?: string;
  userName?: string;
  userEmail?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (avatarUrl: string) => void;
}

export function AvatarUpload({
  userId,
  currentAvatarUrl,
  userName,
  userEmail,
  open,
  onOpenChange,
  onSuccess
}: AvatarUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getInitials = (name?: string, email?: string) => {
    const displayName = name || email || 'User';
    return displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (5MB limit)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setError('Image must be smaller than 5MB');
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setUploadProgress(0);
      setError(null);

      const formData = new FormData();
      formData.append('avatar', selectedFile);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const next = prev + 10;
          return next >= 90 ? 90 : next;
        });
      }, 200);

      const response = await apiClient.request(`/users/${userId}/avatar`, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Wait a moment to show 100% progress
      setTimeout(() => {
        onSuccess?.(response.avatar_url || `/api/v1/users/${userId}/avatar?t=${Date.now()}`);
        handleClose();
        toast({
          title: 'Success',
          description: 'Avatar uploaded successfully',
        });
      }, 500);
    } catch (err: any) {
      console.error('Avatar upload failed:', err);
      setError(err.message || 'Failed to upload avatar');
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveAvatar = async () => {
    try {
      setUploading(true);
      setError(null);

      await apiClient.request(`/users/${userId}/avatar`, {
        method: 'DELETE',
      });

      onSuccess?.('');
      handleClose();
      toast({
        title: 'Success',
        description: 'Avatar removed successfully',
      });
    } catch (err: any) {
      console.error('Failed to remove avatar:', err);
      setError(err.message || 'Failed to remove avatar');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadProgress(0);
    setError(null);
    onOpenChange(false);
    
    // Clean up preview URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  };

  const displayAvatarUrl = previewUrl || currentAvatarUrl;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Camera className="h-5 w-5" />
            <span>Update Avatar</span>
          </DialogTitle>
          <DialogDescription>
            Upload a new profile picture for {userName || userEmail}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Current/Preview Avatar */}
          <div className="flex justify-center">
            <div className="relative">
              <Avatar className="h-32 w-32">
                {displayAvatarUrl ? (
                  <AvatarImage src={displayAvatarUrl} alt="Avatar preview" />
                ) : (
                  <AvatarFallback className="text-2xl">
                    {getInitials(userName, userEmail)}
                  </AvatarFallback>
                )}
              </Avatar>
              
              {displayAvatarUrl && (
                <Button
                  variant="destructive"
                  size="sm"
                  className="absolute -top-2 -right-2 h-6 w-6 rounded-full p-0"
                  onClick={() => {
                    if (previewUrl) {
                      URL.revokeObjectURL(previewUrl);
                      setPreviewUrl(null);
                      setSelectedFile(null);
                    } else {
                      handleRemoveAvatar();
                    }
                  }}
                  disabled={uploading}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>

          {/* Upload Progress */}
          {uploading && uploadProgress > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />

          {/* Upload Guidelines */}
          <div className="text-sm text-muted-foreground space-y-1">
            <p>Guidelines for profile pictures:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Use a square image for best results</li>
              <li>Maximum file size: 5MB</li>
              <li>Supported formats: JPG, PNG, GIF, WebP</li>
              <li>Recommended size: 400x400 pixels or larger</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <div className="flex w-full justify-between">
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <Upload className="h-4 w-4 mr-2" />
                Choose Image
              </Button>
              
              {currentAvatarUrl && !previewUrl && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleRemoveAvatar}
                  disabled={uploading}
                >
                  <X className="h-4 w-4 mr-2" />
                  Remove
                </Button>
              )}
            </div>
            
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={uploading}
              >
                Cancel
              </Button>
              
              {selectedFile && (
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                >
                  <Camera className="h-4 w-4 mr-2" />
                  Upload Avatar
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}