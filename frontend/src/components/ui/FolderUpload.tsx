import { useRef, useState, DragEvent, ChangeEvent } from 'react';

interface FolderUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  title?: string;
  subtitle?: string;
  hint?: string;
}

export function FolderUpload({ 
  onFileSelect, 
  accept = ".csv,.xlsx", 
  title = "Drag & drop your file here", 
  subtitle = "or click to browse files",
  hint = "Accepts .csv and .xlsx · Max 50MB"
}: FolderUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div 
      className={`folder-container ${dragOver ? 'folder-container--dragover' : ''}`}
      onClick={() => fileInputRef.current?.click()}
      onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      role="button" 
      tabIndex={0}
      aria-label="Upload file"
    >
      <div className="folder">
        <div className="front-side">
          <div className="tip"></div>
          <div className="cover"></div>
        </div>
        <div className="back-side cover"></div>
      </div>
      
      <div className="folder-text-wrap">
        <div className="folder-title">{title}</div>
        <div className="folder-sub">{subtitle}</div>
        <div className="folder-hint">{hint}</div>
      </div>
      
      <input 
        ref={fileInputRef} 
        type="file" 
        accept={accept}
        style={{ display: 'none' }} 
        onChange={handleFileChange} 
      />
    </div>
  );
}
