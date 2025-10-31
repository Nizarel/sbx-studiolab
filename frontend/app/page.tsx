"use client"

import { StarbucksBanner } from "@/components/starbucks-banner";
import NewImagePage from "./new-image/page";

export default function HomePage() {
  return (
    <div className="w-full">
      <div className="container mx-auto px-4 py-6">
        <StarbucksBanner />
      </div>
      <NewImagePage />
    </div>
  );
}
