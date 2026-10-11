/** Original decorative flower art (placeholder when product has no photo). */
export default function FlowerArt({ seed = 7, className = "" }: { seed?: number; className?: string }) {
  const petals = 10 + (seed % 8);
  const cx = 200;
  const cy = 185;
  const R = 95;
  const ells = [];
  for (let i = 0; i < petals; i++) {
    const a = (i / petals) * Math.PI * 2;
    const x = cx + Math.cos(a) * R * 0.62;
    const y = cy + Math.sin(a) * R * 0.62;
    ells.push(
      <ellipse key={i} cx={x.toFixed(1)} cy={y.toFixed(1)} rx={(R * 0.42).toFixed(1)} ry={(R * 0.24).toFixed(1)}
        fill="#EBCFD0" opacity="0.95" transform={`rotate(${(a * 180 / Math.PI).toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})`} />
    );
  }
  return (
    <svg viewBox="0 0 400 380" className={className} role="img" aria-label="flower illustration">
      <defs>
        <linearGradient id={`fa-${seed}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FAF8F3" />
          <stop offset="1" stopColor="#DCE5D8" />
        </linearGradient>
      </defs>
      <rect width="400" height="380" fill={`url(#fa-${seed})`} />
      <path d={`M${cx - 70} 350 Q ${cx - 30} 260 ${cx - 8} ${cy + 40} Q ${cx - 50} 290 ${cx - 70} 350Z`} fill="#233C32" opacity="0.85" />
      <path d={`M${cx + 70} 350 Q ${cx + 30} 260 ${cx + 8} ${cy + 40} Q ${cx + 50} 290 ${cx + 70} 350Z`} fill="#2e5245" opacity="0.85" />
      {ells}
      <circle cx={cx} cy={cy} r={(R * 0.34).toFixed(1)} fill="#E8C872" />
      <circle cx={cx - R * 0.1} cy={cy - R * 0.12} r={(R * 0.07).toFixed(1)} fill="#ffffffaa" />
    </svg>
  );
}
