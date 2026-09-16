"use client";

import Image from "next/image";
import { useState } from "react";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { assetUrl } from "@/lib/api";
import type { ApplicationFileOut } from "@/lib/types";

const FILE_TYPE_LABELS: Record<string, string> = {
  METER_PHOTO: "Есептеу құралының фотосы",
  GAS_LEAK_PHOTO: "Газ шығып жатқан жердің фотосы",
  OTHER: "Фото",
};

export function PhotoLightbox({ files }: { files: ApplicationFileOut[] }) {
  const [active, setActive] = useState<ApplicationFileOut | null>(null);

  if (files.length === 0) {
    return <p className="text-sm text-muted-foreground">Фотосуреттер жоқ</p>;
  }

  return (
    <>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {files.map((file) => (
          <button
            key={file.id}
            onClick={() => setActive(file)}
            className="group flex flex-col gap-1 overflow-hidden rounded-md border border-border text-left"
          >
            <div className="relative h-32 w-full bg-muted">
              <Image
                src={assetUrl(file.storage_url)}
                alt={FILE_TYPE_LABELS[file.file_type] ?? "Фото"}
                fill
                unoptimized
                className="object-cover transition-transform group-hover:scale-105"
              />
            </div>
            <span className="px-2 pb-2 text-xs text-muted-foreground">{FILE_TYPE_LABELS[file.file_type]}</span>
          </button>
        ))}
      </div>

      <Dialog open={!!active} onOpenChange={(open) => !open && setActive(null)}>
        <DialogContent className="max-w-3xl bg-transparent p-0 shadow-none">
          <DialogTitle className="sr-only">{active ? FILE_TYPE_LABELS[active.file_type] : "Фото"}</DialogTitle>
          {active && (
            <div className="relative h-[80vh] w-full">
              <Image
                src={assetUrl(active.storage_url)}
                alt={FILE_TYPE_LABELS[active.file_type] ?? "Фото"}
                fill
                unoptimized
                className="object-contain"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
