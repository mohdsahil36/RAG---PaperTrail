import { Workspace } from "@/components/workspace";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh">
      <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface px-4 sm:px-5">
        <Logo />
        <div className="flex min-w-0 items-baseline gap-2.5">
          <h1 className="text-[15px] font-semibold tracking-tight text-ink">Papertrail</h1>
          <p className="hidden truncate text-sm text-ink-subtle sm:block">
            Your documents, ready to explore.
          </p>
        </div>
      </header>
      <Workspace />
    </div>
  );
}

function Logo() {
  return (
    <svg viewBox="0 0 24 24" className="size-7 shrink-0" aria-hidden>
      <rect width="24" height="24" rx="6" className="fill-accent" />
      <path d="M8 6h5.5L17 9.5V18H8z" fill="white" />
      <path d="M13.5 6v3.5H17" fill="none" className="stroke-accent" strokeWidth="1.2" />
      <path d="M10 12.5h5M10 15h3.5" className="stroke-accent" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}
