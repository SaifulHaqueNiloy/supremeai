import React from 'react';

// ============================================
// SupremeCard Component
// ============================================
interface SupremeCardProps {
  children: React.ReactNode;
  accent?: 'primary' | 'success' | 'info' | 'warning' | 'danger';
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const SupremeCard: React.FC<SupremeCardProps> = ({
  children,
  accent = 'primary',
  className = '',
  onClick,
  hoverable = true,
}) => {
  return (
    <div
      className={`supreme-glass rounded-xl p-5 border border-white/10 ${
        hoverable ? 'supreme-glass-hover cursor-pointer' : ''
      } accent-${accent} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

// ============================================
// SupremeButton Component
// ============================================
interface SupremeButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

export const SupremeButton: React.FC<SupremeButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  disabled = false,
  onClick,
  className = '',
}) => {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantClasses = {
    primary: 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/20',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700',
    success: 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20',
    danger: 'bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-lg shadow-rose-500/20',
    ghost: 'bg-transparent hover:bg-slate-800/50 text-slate-300 hover:text-white',
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:pointer-events-none ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
};

// ============================================
// SupremeBadge Component
// ============================================
interface SupremeBadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  pulse?: boolean;
  className?: string;
}

export const SupremeBadge: React.FC<SupremeBadgeProps> = ({
  children,
  variant = 'primary',
  pulse = false,
  className = '',
}) => {
  const variantClasses = {
    primary: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    info: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantClasses[variant]} ${className}`}>
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
        </span>
      )}
      {children}
    </span>
  );
};
