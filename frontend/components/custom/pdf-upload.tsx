"use client"

import { useRef, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"
import { uploadPdf } from "@/lib/api"
import { toast } from "sonner"

interface PdfUploadProps {
  onFileUploaded?: () => void
}

export function PdfUpload({ onFileUploaded } : PdfUploadProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleUpload = async (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()

    if (!file) return

    try {
      setUploading(true)
      await uploadPdf(file)
      toast.info("File uploaded successfully.")
      if (onFileUploaded) {
        onFileUploaded()
      }

      setFile(null)

      if (inputRef.current) {
        inputRef.current.value = ""
      }
    } catch (error) {
      console.error(error)
      toast.error("File couldn't be uploaded. Please try again later.")
    } finally {
      setUploading(false)
    }
  }

  return (
    <>
      <input
        type="file"
        accept="application/pdf"
        ref={inputRef}
        onChange={handleChange}
        className="hidden"
      />

      <Card
        onClick={handleClick}
        className="cursor-pointer border-dashed border-2 hover:bg-muted/40 transition-colors"
      >
        <CardContent className="flex flex-col items-center justify-center p-1 space-y-3">
            <Upload className="w-8 h-8 text-muted-foreground" />

            <div className="text-sm text-muted-foreground">
                {file ? file.name : "Click here to upload a PDF file"}
            </div>

            {uploading ? <p className="animate-pulse">Uploading...</p> :
            <div className="flex flex-row gap-2">
                <Button variant="secondary" type="button">
                    Select File
                </Button>
                {file !== null ?
                    <Button onClick={(event) => handleUpload(event)} className="z-100" type="button">
                        Upload File
                    </Button>
                    : <></>
                }
            </div>}

        </CardContent>
      </Card>
    </>
  )
}
