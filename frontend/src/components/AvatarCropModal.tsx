"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { X, ZoomIn, ZoomOut, RotateCcw, Check, Move, Crop, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { springs } from "@/lib/motion-tokens";
import { ClientPortal } from "./ClientPortal";

interface AvatarCropModalProps {
  imageSrc: string;
  onCrop: (croppedDataUrl: string) => void;
  onClose: () => void;
}

export const AvatarCropModal: React.FC<AvatarCropModalProps> = ({
  imageSrc,
  onCrop,
  onClose,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [imgNaturalSize, setImgNaturalSize] = useState({ width: 0, height: 0 });
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const VIEWPORT_SIZE = 260;
  const OUTPUT_SIZE = 256;

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImgNaturalSize({ width: img.naturalWidth, height: img.naturalHeight });
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({
      x: e.clientX - pan.x,
      y: e.clientY - pan.y,
    });
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    const maxBound = (VIEWPORT_SIZE * (zoom - 1 + 0.5)) / 2;
    const newX = e.clientX - dragStart.x;
    const newY = e.clientY - dragStart.y;
    setPan({
      x: Math.max(-maxBound, Math.min(maxBound, newX)),
      y: Math.max(-maxBound, Math.min(maxBound, newY)),
    });
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    setIsDragging(false);
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const zoomDelta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom((prev) => Math.max(1, Math.min(3, +(prev + zoomDelta).toFixed(2))));
  };

  const generateCropDataUrl = useCallback((): string | null => {
    if (!imageRef.current || imgNaturalSize.width === 0 || imgNaturalSize.height === 0) {
      return null;
    }

    const canvas = document.createElement("canvas");
    canvas.width = OUTPUT_SIZE;
    canvas.height = OUTPUT_SIZE;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    ctx.save();
    ctx.beginPath();
    ctx.arc(OUTPUT_SIZE / 2, OUTPUT_SIZE / 2, OUTPUT_SIZE / 2, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.clip();

    const scale = (OUTPUT_SIZE / VIEWPORT_SIZE) * zoom;
    const imgAspect = imgNaturalSize.width / imgNaturalSize.height;

    let drawWidth: number;
    let drawHeight: number;

    if (imgAspect > 1) {
      drawHeight = OUTPUT_SIZE * zoom;
      drawWidth = drawHeight * imgAspect;
    } else {
      drawWidth = OUTPUT_SIZE * zoom;
      drawHeight = drawWidth / imgAspect;
    }

    const drawX = (OUTPUT_SIZE - drawWidth) / 2 + (pan.x * OUTPUT_SIZE) / VIEWPORT_SIZE;
    const drawY = (OUTPUT_SIZE - drawHeight) / 2 + (pan.y * OUTPUT_SIZE) / VIEWPORT_SIZE;

    ctx.drawImage(imageRef.current, drawX, drawY, drawWidth, drawHeight);
    ctx.restore();

    return canvas.toDataURL("image/jpeg", 0.88);
  }, [imgNaturalSize, pan, zoom]);

  useEffect(() => {
    if (imgNaturalSize.width > 0) {
      const live = generateCropDataUrl();
      if (live) setPreviewUrl(live);
    }
  }, [imgNaturalSize, pan, zoom, generateCropDataUrl]);

  const handleApply = () => {
    const cropped = generateCropDataUrl();
    if (cropped) {
      onCrop(cropped);
    }
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <ClientPortal>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-md"
          onClick={onClose}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={springs.gentle}
          className="relative w-full max-w-md bg-white dark:bg-[#0B101B] border border-stone-300 dark:border-slate-800 rounded-3xl shadow-2xl overflow-hidden z-10 flex flex-col"
        >
          <div className="h-1.5 gold-ribbon w-full" />

          <div className="p-5 border-b border-stone-200 dark:border-slate-800 flex items-center justify-between bg-stone-50/70 dark:bg-[#0E1524]">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                <Crop className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-serif font-bold text-slate-900 dark:text-slate-50 text-base leading-tight">
                  Crop Profile Picture
                </h3>
                <p className="text-[11px] text-stone-500 dark:text-slate-400 font-mono">
                  Drag to reposition • Zoom to frame
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-stone-400 hover:text-stone-700 dark:hover:text-slate-200 rounded-xl hover:bg-stone-200/60 dark:hover:bg-slate-800 transition-colors"
              aria-label="Close Crop Modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="p-6 flex flex-col items-center gap-5">
            <div
              ref={containerRef}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerCancel={handlePointerUp}
              onWheel={handleWheel}
              style={{ width: VIEWPORT_SIZE, height: VIEWPORT_SIZE }}
              className={`relative overflow-hidden rounded-full bg-slate-950 select-none touch-none border-2 border-amber-500 shadow-xl ${
                isDragging ? "cursor-grabbing" : "cursor-grab"
              }`}
            >
              <img
                ref={imageRef}
                src={imageSrc}
                alt="Source Crop"
                onLoad={handleImageLoad}
                draggable={false}
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                  transformOrigin: "center center",
                  transition: isDragging ? "none" : "transform 0.1s ease-out",
                }}
                className="w-full h-full object-cover pointer-events-none"
              />

              <div className="absolute inset-0 pointer-events-none rounded-full ring-1 ring-white/20 grid grid-cols-3 grid-rows-3 opacity-30">
                <div className="border-r border-b border-white/40" />
                <div className="border-r border-b border-white/40" />
                <div className="border-b border-white/40" />
                <div className="border-r border-b border-white/40" />
                <div className="border-r border-b border-white/40" />
                <div className="border-b border-white/40" />
                <div className="border-r border-white/40" />
                <div className="border-r border-white/40" />
                <div />
              </div>

              {!isDragging && (
                <div className="absolute bottom-2 inset-x-0 flex justify-center pointer-events-none">
                  <span className="bg-slate-950/75 text-white/90 text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1 border border-white/10 shadow-xs">
                    <Move className="h-3 w-3" />
                    <span>Drag to move</span>
                  </span>
                </div>
              )}
            </div>

            <div className="w-full space-y-3 px-2">
              <div className="flex items-center justify-between text-xs font-semibold text-stone-700 dark:text-slate-300">
                <span className="flex items-center gap-1">
                  <ZoomIn className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                  <span>Zoom Level</span>
                </span>
                <span className="font-mono text-amber-700 dark:text-amber-400">
                  {Math.round(zoom * 100)}%
                </span>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setZoom((prev) => Math.max(1, +(prev - 0.2).toFixed(2)))}
                  className="p-1.5 rounded-lg border border-stone-300 dark:border-slate-700 hover:bg-stone-100 dark:hover:bg-slate-800 text-stone-700 dark:text-slate-300 transition-colors"
                  aria-label="Zoom Out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>

                <input
                  type="range"
                  min="1"
                  max="3"
                  step="0.05"
                  value={zoom}
                  onChange={(e) => setZoom(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-stone-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-600"
                />

                <button
                  type="button"
                  onClick={() => setZoom((prev) => Math.min(3, +(prev + 0.2).toFixed(2)))}
                  className="p-1.5 rounded-lg border border-stone-300 dark:border-slate-700 hover:bg-stone-100 dark:hover:bg-slate-800 text-stone-700 dark:text-slate-300 transition-colors"
                  aria-label="Zoom In"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>

                <button
                  type="button"
                  onClick={handleReset}
                  title="Reset Position and Zoom"
                  className="p-1.5 rounded-lg border border-stone-300 dark:border-slate-700 hover:bg-stone-100 dark:hover:bg-slate-800 text-stone-700 dark:text-slate-300 transition-colors"
                  aria-label="Reset Crop"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>
            </div>

            {previewUrl && (
              <div className="flex items-center gap-3 p-3 w-full rounded-2xl bg-stone-50 dark:bg-slate-900/60 border border-stone-200 dark:border-slate-800">
                <img
                  src={previewUrl}
                  alt="Live Preview"
                  className="h-10 w-10 rounded-full object-cover border border-amber-500/50 shadow-xs"
                />
                <div className="flex-1 overflow-hidden">
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5 font-serif">
                    <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                    <span>Live Output Preview</span>
                  </p>
                  <p className="text-[10px] text-stone-500 dark:text-slate-400 font-mono">
                    256 × 256 px • Compressed JPEG
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-stone-200 dark:border-slate-800 bg-stone-50/60 dark:bg-[#0E1524] flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 dark:text-slate-400 hover:bg-stone-200 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="royal-btn-gold font-bold px-5 py-2 rounded-xl text-xs flex items-center gap-1.5 shadow-xs active:scale-[0.98]"
            >
              <Check className="h-4 w-4" />
              <span>Apply Crop</span>
            </button>
          </div>
        </motion.div>
      </div>
    </ClientPortal>
  );
};
