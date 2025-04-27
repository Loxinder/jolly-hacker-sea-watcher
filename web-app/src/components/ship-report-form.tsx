"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { MapPin, AlertCircle, Ship, Upload, Check, Camera, LogOut, Star } from "lucide-react"

// Default API endpoint with fallback
const API_ENDPOINT = process.env.SUBMIT_SHIP_ENDPOINT || 'http://localhost:8001/submit_ship';

// Add activity types interface
const ACTIVITY_TYPES = [
  { id: 'trespassing', label: 'Territorial Waters Trespassing' },
  { id: 'fishing', label: 'Illegal Fishing' },
  { id: 'pirating', label: 'Pirating Activity' },
  { id: 'smuggling', label: 'Suspected Smuggling' },
  { id: 'environmental', label: 'Environmental Violation' },
  { id: 'other', label: 'Other Suspicious Activity' },
] as const;

// Add vessel headings interface
const VESSEL_HEADINGS = [
  { id: 'N', label: 'North' },
  { id: 'E', label: 'East' },
  { id: 'S', label: 'South' },
  { id: 'W', label: 'West' },
  { id: 'docked', label: 'Docked' },
  { id: 'stationary', label: 'Stationary' },
  { id: 'unknown', label: 'Unknown' },
] as const;

// Add vessel registry flags
const VESSEL_REGISTRY_FLAGS = [
  { code: '🇺🇸', name: 'United States' },
  { code: '🇬🇧', name: 'United Kingdom' },
  { code: '🇨🇦', name: 'Canada' },
  { code: '🇦🇺', name: 'Australia' },
  { code: '🇳🇿', name: 'New Zealand' },
  { code: '🇯🇵', name: 'Japan' },
  { code: '🇨🇳', name: 'China' },
  { code: '🇷🇺', name: 'Russia' },
  { code: '🇮🇳', name: 'India' },
  { code: '🇧🇷', name: 'Brazil' },
  { code: '🇵🇦', name: 'Panama' },
  { code: '🇱🇷', name: 'Liberia' },
  { code: '🇲🇭', name: 'Marshall Islands' },
  { code: '🇸🇬', name: 'Singapore' },
  { code: '🇳🇴', name: 'Norway' },
  { code: '🇬🇷', name: 'Greece' },
  { code: '🇲🇹', name: 'Malta' },
  { code: '🇨🇾', name: 'Cyprus' },
  { code: '🇮🇹', name: 'Italy' },
  { code: '🇫🇷', name: 'France' },
  { code: '🇩🇪', name: 'Germany' },
  { code: '🇳🇱', name: 'Netherlands' },
  { code: '🇪🇸', name: 'Spain' },
  { code: '🇵🇹', name: 'Portugal' },
  { code: '🇩🇰', name: 'Denmark' },
  { code: '🇸🇪', name: 'Sweden' },
  { code: '🇫🇮', name: 'Finland' },
] as const;

interface ShipReportFormProps {
  user: { id: string; name: string; score: number } | null
  onLogout: () => void
}

export default function ShipReportForm({ user, onLogout }: ShipReportFormProps) {
  const [description, setDescription] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [isGettingLocation, setIsGettingLocation] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [activityType, setActivityType] = useState<string>('')
  const [vesselHeading, setVesselHeading] = useState<string>('')
  const [vesselRegistry, setVesselRegistry] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setImage(file)

      // Create preview
      const reader = new FileReader()
      reader.onload = (event) => {
        setImagePreview(event.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const getLocation = () => {
    setIsGettingLocation(true)
    setLocationError(null)

    if (!navigator.geolocation) {
      setLocationError("Geolocation is not supported by your browser")
      setIsGettingLocation(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
        setIsGettingLocation(false)
      },
      (error) => {
        setLocationError(`Error getting location: ${error.message}`)
        setIsGettingLocation(false)
      },
    )
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setIsCameraActive(true)
      }
    } catch (err) {
      console.error("Error accessing camera:", err)
      alert("Could not access the camera. Please check your permissions.")
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setIsCameraActive(false)
  }

  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current
      const canvas = canvasRef.current

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      // Draw the video frame to the canvas
      const context = canvas.getContext("2d")
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert canvas to file
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const file = new File([blob], "camera-photo.jpg", { type: "image/jpeg" })
              setImage(file)
              setImagePreview(canvas.toDataURL("image/jpeg"))
              stopCamera()
            }
          },
          "image/jpeg",
          0.95,
        )
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setFormError(null)

    // Check if either image or location is provided
    if (!image && !location) {
      setFormError("Either an image or location is required to submit a report")
      setIsSubmitting(false)
      return
    }

    try {
      // Create a timestamp 
      const timestamp = new Date().toISOString();
      
      // Convert image to base64 if available
      let base64Image = null;
      if (image) {
        base64Image = await convertImageToBase64(image);
      }
      
      // Prepare the API payload according to the required structure
      const apiPayload = {
        source_account_id: user?.id || "anonymous",
        timestamp: timestamp,
        latitude: location?.latitude,
        longitude: location?.longitude,
        picture_url: base64Image, // Using base64 image data
        description: description || undefined,
        activity_type: activityType || undefined,
        vessel_heading: vesselHeading || undefined,
        vessel_registry: vesselRegistry || undefined,
      };
      
      console.log("Sending payload to API:", apiPayload);
      
      // Send the API request
      const response = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(apiPayload),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      console.log("API response:", data);

      // On success
      setIsSubmitting(false)
      setIsSuccess(true)

      // Reset form after 3 seconds
      setTimeout(() => {
        setDescription("")
        setImage(null)
        setImagePreview(null)
        setVesselRegistry("")
        setIsSuccess(false)
      }, 3000)
    } catch (error) {
      console.error("Error submitting form:", error);
      setIsSubmitting(false)
      alert("Failed to submit report. Please try again.");
    }
  }

  // Helper function to convert an image file to a base64 string
  const convertImageToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to convert image to base64'));
        }
      };
      reader.onerror = () => {
        reject(new Error('Failed to read image file'));
      };
      reader.readAsDataURL(file);
    });
  };

  // Function to render stars based on score
  const renderStars = (score: number) => {
    const stars = [];
    const maxDisplayedStars = 5;
    const fullStars = Math.min(score, maxDisplayedStars);
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <Star key={i} className="h-6 w-6 fill-yellow-400 text-yellow-400" />
      );
    }
    
    // Add empty stars to complete the set
    for (let i = fullStars; i < maxDisplayedStars; i++) {
      stars.push(
        <Star key={i + 'empty'} className="h-6 w-6 text-gray-300" />
      );
    }
    
    return stars;
  };

  // Clean up camera stream on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [])

  return (
    <div className="space-y-4">
      {isSuccess ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-600" />
            <h4 className="font-medium">Success!</h4>
          </div>
          <p className="text-sm mt-1">Your ship report has been submitted successfully.</p>
        </div>
      ) : isCameraActive ? (
        <div className="space-y-4">
          <div className="relative">
            <video ref={videoRef} autoPlay playsInline className="w-full rounded-md border border-gray-300" />
            <canvas ref={canvasRef} className="hidden" />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={takePhoto}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Camera className="h-4 w-4" />
              Take Photo
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Either an image or location is required to submit a report. Other fields are optional.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium">Send Image</label>
            {imagePreview ? (
              <div className="border rounded-md p-2">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-h-40 mx-auto object-contain rounded-md"
                />
                <div className="flex gap-2 mt-2">
                  <button
                    type="button"
                    className="flex-1 px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50"
                    onClick={() => {
                      setImage(null)
                      setImagePreview(null)
                      if (fileInputRef.current) fileInputRef.current.value = ""
                    }}
                  >
                    Remove
                  </button>
                  <button
                    type="button"
                    className="flex-1 px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Change
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  type="button"
                  className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4" />
                  Upload Image
                </button>
                <button
                  type="button"
                  className="flex-1 border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2"
                  onClick={startCamera}
                >
                  <Camera className="h-4 w-4" />
                  Take Photo
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageChange}
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium">Send Location</label>
            {location ? (
              <div className="p-3 bg-gray-100 rounded-md">
                <div className="flex items-center text-sm">
                  <MapPin className="h-4 w-4 mr-2 text-gray-500" />
                  <span>
                    Lat: {location.latitude.toFixed(6)}, Long: {location.longitude.toFixed(6)}
                  </span>
                </div>
              </div>
            ) : (
              <button
                type="button"
                className="w-full border px-4 py-2 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={getLocation}
                disabled={isGettingLocation}
              >
                <MapPin className="h-4 w-4" />
                {isGettingLocation ? "Getting location..." : "Get Current Location"}
              </button>
            )}

            {locationError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <h4 className="font-medium">Error</h4>
                </div>
                <p className="text-sm mt-1">{locationError}</p>
              </div>
            )}
          </div>

          {/* Activity Type Dropdown */}
          <div className="space-y-1">
            <label htmlFor="activityType" className="block text-sm font-medium">
              Activity Type
            </label>
            <select
              id="activityType"
              value={activityType}
              onChange={(e) => setActivityType(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">Select activity type...</option>
              {ACTIVITY_TYPES.map(type => (
                <option key={type.id} value={type.id}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Vessel Heading Dropdown */}
          <div className="space-y-1">
            <label htmlFor="vesselHeading" className="block text-sm font-medium">
              Vessel Heading
            </label>
            <select
              id="vesselHeading"
              value={vesselHeading}
              onChange={(e) => setVesselHeading(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">Select vessel heading...</option>
              {VESSEL_HEADINGS.map(heading => (
                <option key={heading.id} value={heading.id}>
                  {heading.label}
                </option>
              ))}
            </select>
          </div>

          {/* Vessel Registry Dropdown */}
          <div className="space-y-1">
            <label htmlFor="vesselRegistry" className="block text-sm font-medium">
              Vessel Registry Flag (Optional)
            </label>
            <select
              id="vesselRegistry"
              value={vesselRegistry}
              onChange={(e) => setVesselRegistry(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              <option value="">Select vessel registry...</option>
              {VESSEL_REGISTRY_FLAGS.map(flag => (
                <option key={flag.code} value={flag.code}>
                  {flag.code} {flag.name}
                </option>
              ))}
            </select>
          </div>

          {/* Details textarea now comes after activity type */}
          <div className="space-y-1">
            <label htmlFor="description" className="block text-sm font-medium">
              Provide Details
            </label>
            <textarea
              id="description"
              className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Describe the ship you saw..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting || (!image && !location)}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Ship className="h-4 w-4" />
            {isSubmitting ? "Submitting..." : "Submit Report"}
          </button>

          {formError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <h4 className="font-medium">Error</h4>
              </div>
              <p className="text-sm mt-1">{formError}</p>
            </div>
          )}

          {user?.id === "guest" && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <h4 className="font-medium">Guest Mode</h4>
              </div>
              <p className="text-sm mt-1">You're reporting as a guest. Your report will be anonymous.</p>
            </div>
          )}

          {/* Maritime Observer Status and User Info */}
          <div className="mt-8 pt-4 border-t">
            {/* Observer Status */}
            {user && (
              <div className="mb-4 bg-gradient-to-b from-blue-50 to-white p-4 rounded-lg border border-blue-100">
                <p className="text-sm font-medium text-gray-500 mb-1 text-center">MARITIME OBSERVER STATUS</p>
                
                <div className="flex justify-center gap-1 mb-1">
                  {renderStars(user.score)}
                </div>
                
                {user.score > 0 ? (
                  <p className="text-sm text-center font-medium text-gray-700 mt-1">
                    {user.score >= 5 ? 
                      "Maritime Security Specialist" : 
                      user.score >= 3 ? 
                        "Verified Coastal Monitor" : 
                        "Qualified Maritime Observer"}
                  </p>
                ) : (
                  <p className="text-xs text-center text-gray-500 mt-1">
                    Submit your first report to establish credentials
                  </p>
                )}
              </div>
            )}
            
            {/* User info and logout */}
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-500">Logged in as</p>
                <p className="text-sm font-semibold">{user?.name}</p>
              </div>
              <button
                onClick={onLogout}
                className="px-3 py-1.5 text-sm border rounded-md hover:bg-gray-50 flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}