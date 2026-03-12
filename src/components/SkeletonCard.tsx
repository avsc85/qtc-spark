const SkeletonCard = () => (
  <div className="glass-card p-6 space-y-3">
    <div className="skeleton-shimmer h-4 w-24" />
    <div className="skeleton-shimmer h-8 w-32" />
    <div className="skeleton-shimmer h-3 w-20" />
  </div>
);

export const SkeletonRow = () => (
  <div className="flex items-center gap-4 p-4">
    <div className="skeleton-shimmer h-4 w-32" />
    <div className="skeleton-shimmer h-4 w-20" />
    <div className="skeleton-shimmer h-4 w-24" />
    <div className="skeleton-shimmer h-4 w-16" />
  </div>
);

export default SkeletonCard;
