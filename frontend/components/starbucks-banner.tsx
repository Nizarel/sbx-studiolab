"use client"

import { motion } from "framer-motion";
import { Sparkles, Video, Image as ImageIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export function StarbucksBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-background border-2 border-primary/20 p-6 md:p-8 mb-6"
    >
      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-primary/5 rounded-full blur-3xl -z-10" />
      
      <div className="flex flex-col items-center text-center space-y-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="flex flex-col items-center space-y-3"
        >
          <Image 
            src="/logo/starbucks-logo.svg" 
            alt="Starbucks" 
            width={60} 
            height={60}
            className="drop-shadow-lg"
          />
          <div className="space-y-1">
            <h1 className="text-3xl md:text-5xl font-bold text-primary tracking-tight">
              STARBUCKS® VIDEO STUDIO
            </h1>
            <p className="text-sm md:text-base text-muted-foreground">
              AI-Powered Content Creation
            </p>
          </div>
        </motion.div>
        
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="text-base md:text-lg text-foreground/80 max-w-3xl"
        >
          Create stunning videos and images with the power of AI.
          <span className="text-primary font-semibold"> Get started today</span> and bring your creative vision to life.
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="flex flex-wrap justify-center gap-3 pt-2"
        >
          <Link href="/new-video">
            <div className="flex items-center gap-2 bg-background/50 backdrop-blur px-4 py-2 rounded-full border border-primary/20 hover:bg-primary/10 hover:border-primary/40 transition-all cursor-pointer hover:scale-105">
              <Video className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">AI Video Generation</span>
            </div>
          </Link>
          <Link href="/new-image">
            <div className="flex items-center gap-2 bg-background/50 backdrop-blur px-4 py-2 rounded-full border border-primary/20 hover:bg-primary/10 hover:border-primary/40 transition-all cursor-pointer hover:scale-105">
              <ImageIcon className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Image Creation</span>
            </div>
          </Link>
          <Link href="/analyze">
            <div className="flex items-center gap-2 bg-background/50 backdrop-blur px-4 py-2 rounded-full border border-primary/20 hover:bg-primary/10 hover:border-primary/40 transition-all cursor-pointer hover:scale-105">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Smart Analysis</span>
            </div>
          </Link>
        </motion.div>
      </div>
    </motion.div>
  );
}
