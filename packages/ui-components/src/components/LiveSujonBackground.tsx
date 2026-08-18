export function LiveSujonBackground({ isServerOnline = false }: { isServerOnline?: boolean }) {
  return (
    <div
      aria-hidden
      data-online={isServerOnline}
      className="absolute inset-0 -z-10 bg-gradient-to-b from-[#00111a] to-[#061025]"
    />
  );
}
