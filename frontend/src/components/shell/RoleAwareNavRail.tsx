// SupremeAI — RoleAwareNavRail (single-frontend migration, roadmap Phase 3/6)
// বাংলা মন্তব্য: একটাই sidebar framework — User ও Admin দুই context-ই এটি ব্যবহার করে।
// কনটেন্ট NAVIGATION_REGISTRY থেকে generate হয়; দ্বিতীয় কোনো nav definition নেই।

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getNavigationForContext, type NavEntry } from '../../config/navigationRegistry';

export interface RoleAwareNavRailProps {
  context: 'user' | 'admin';
  collapsed: boolean;
  /** Admin context: currently active subtab id (drives action-item active state). */
  activeActionId?: string;
  /** Admin context: handler for action items (admin subtab switch). */
  onAction?: (actionId: string) => void;
}

export function RoleAwareNavRail({ context, collapsed, activeActionId, onAction }: RoleAwareNavRailProps) {
  const location = useLocation();
  const groups = getNavigationForContext(context);

  // বাংলা: আগের UserSidebar-এর active semantics হুবহু — exact match, অথবা non-root
  // path-এর জন্য prefix match।
  const isRouteActive = (path: string) =>
    location.pathname === path || (path !== '/workspace' && location.pathname.startsWith(path));

  const renderEntry = (item: NavEntry) => {
    const iconEl = (
      <item.icon
        size={18}
        className={item.kind === 'action' && activeActionId === item.actionId ? 'text-accent-primary' : 'text-secondary'}
      />
    );
    const labelEl = !collapsed ? <span>{item.label}</span> : null;
    const baseCls =
      'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200';
    const titleAttr = collapsed ? item.label : undefined;

    if (item.kind === 'route') {
      const active = isRouteActive(item.path);
      return (
        <Link
          key={item.id}
          to={item.path}
          title={titleAttr}
          className={`${baseCls} ${active
            ? 'surface-3 text-accent-primary border-l-2 border-accent-primary'
            : 'text-secondary hover:surface-2 hover:text-text'}`}
        >
          {iconEl}
          {labelEl}
        </Link>
      );
    }

    const active = activeActionId === item.actionId;
    return (
      <button
        key={item.id}
        type="button"
        title={titleAttr}
        onClick={() => onAction?.(item.actionId)}
        className={`${baseCls} ${active
          ? 'surface-3 text-accent-primary border-l-2 border-accent-primary'
          : 'text-secondary hover:surface-2 hover:text-text'}`}
      >
        {iconEl}
        {labelEl}
      </button>
    );
  };

  return (
    <div className="flex flex-col h-full py-4 bg-surface-1 overflow-y-auto w-full">
      <div className="flex-1 px-3 space-y-6">
        {groups.map((group) => (
          <div key={group.id} className="space-y-1">
            {!collapsed && (
              <div className="px-3 mb-2 text-[10px] font-bold text-muted uppercase tracking-widest">
                {group.label}
              </div>
            )}
            {group.items.map(renderEntry)}
          </div>
        ))}
      </div>

      {!collapsed && context === 'admin' && (
        <div className="px-6 border-t border-border pt-4 mt-4">
          <div className="text-[9px] text-muted text-center font-mono">
            CTRL+K for command menu
          </div>
        </div>
      )}
    </div>
  );
}
