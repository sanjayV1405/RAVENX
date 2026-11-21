import Link from "next/link";
import { FileQuestion, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-6 select-none">
      <div className="w-16 h-16 rounded-3xl bg-red-50/80 border border-red-100 flex items-center justify-center text-[#DC2626] mb-5 shadow-sm">
        <FileQuestion className="w-8 h-8" />
      </div>

      <span className="text-xs font-mono font-bold uppercase tracking-widest text-[#DC2626] mb-1">
        404 — Page Not Found
      </span>

      <h1 className="text-3xl font-black text-[#1A1D26] tracking-tight">
        Document or Route Not Located
      </h1>

      <p className="text-xs md:text-sm text-[#687080] max-w-md mt-2 leading-relaxed">
        The requested document inspection view or resource could not be found. Return to the Command Center to continue your analysis.
      </p>

      <div className="mt-6 flex items-center gap-3">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs md:text-sm font-semibold aurora-btn-crimson"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Command Center</span>
        </Link>
      </div>
    </div>
  );
}
