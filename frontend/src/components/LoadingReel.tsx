export function LoadingReel({
  message = "Researching claims...",
}: {
  message?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-6 py-16">
      <div className="relative h-16 w-16">
        <div className="absolute inset-0 rounded-full border-2 border-charcoal-light" />
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-r-amber/40 border-t-amber" />
        <div className="absolute inset-2 flex items-center justify-center text-xl">
          🎞️
        </div>
      </div>
      <div className="text-center">
        <p className="font-display text-lg text-parchment">{message}</p>
        <p className="mt-1 text-sm text-parchment/50">
          Extracting claims and verifying with live research...
        </p>
      </div>
    </div>
  );
}
