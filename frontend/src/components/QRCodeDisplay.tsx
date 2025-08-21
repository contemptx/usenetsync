import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Copy, Download, Share2 } from 'lucide-react';
import { Button } from './ui/button';

interface QRCodeDisplayProps {
  value: string;
  size?: number;
  level?: 'L' | 'M' | 'Q' | 'H';
  includeMargin?: boolean;
  title?: string;
  showActions?: boolean;
}

export function QRCodeDisplay({
  value,
  size = 256,
  level = 'M',
  includeMargin = true,
  title,
  showActions = true
}: QRCodeDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleDownload = () => {
    const svg = document.getElementById('qr-code-svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = size;
      canvas.height = size;
      ctx?.drawImage(img, 0, 0);
      
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `qr-code-${Date.now()}.png`;
          a.click();
          URL.revokeObjectURL(url);
        }
      });
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: title || 'QR Code',
          text: value,
          url: value.startsWith('http') ? value : undefined
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg">
      {title && (
        <h3 className="text-lg font-semibold">{title}</h3>
      )}
      
      <div className="p-4 bg-white rounded-lg">
        <QRCodeSVG
          id="qr-code-svg"
          value={value}
          size={size}
          level={level}
          includeMargin={includeMargin}
        />
      </div>

      <div className="w-full max-w-sm">
        <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono break-all">
          {value}
        </div>
      </div>

      {showActions && (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="flex items-center gap-1"
          >
            <Copy className="h-4 w-4" />
            {copied ? 'Copied!' : 'Copy'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            className="flex items-center gap-1"
          >
            <Download className="h-4 w-4" />
            Download
          </Button>
          
          {navigator.share && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
              className="flex items-center gap-1"
            >
              <Share2 className="h-4 w-4" />
              Share
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default QRCodeDisplay;