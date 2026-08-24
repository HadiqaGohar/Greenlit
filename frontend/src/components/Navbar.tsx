"use client";

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sun, Moon, Bell, User, Settings } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getNotifications } from '@/lib/api';

export default function Navbar() {
  const { user, signOut } = useAuth();
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) return;
    const fetchNotifications = async () => {
      try {
        const data = await getNotifications(user.uid, true);
        setUnreadCount(data.unread_count);
      } catch {}
    };
    fetchNotifications();
    // Poll every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const handleSignOut = async () => {
    await signOut();
    router.push('/');
  };

  return (
    <nav className="border-b" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surface)' }}>
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            <span className="font-display font-bold text-lg" style={{ color: 'var(--text)' }}>
              GreenLit AI
            </span>
          </Link>

          {/* Center spacer - navigation moved to Sidebar */}

          {/* Right side - Theme toggle, notifications, user menu */}
          <div className="flex items-center gap-3">
            {/* Keyboard shortcuts hint */}
            <button
              onClick={() => {
                // Dispatch a custom event that the layout listens to
                window.dispatchEvent(new KeyboardEvent("keydown", { key: "?" }));
              }}
              className="hidden sm:flex items-center gap-1 p-1.5 rounded-lg text-xs transition-colors"
              style={{ 
                backgroundColor: 'var(--bg)',
                color: 'var(--text-muted, var(--text))'
              }}
              title="Keyboard shortcuts (?)"
            >
              <kbd className="rounded border border-gray-300 px-1 py-0.5 text-[10px] font-mono dark:border-gray-600">?</kbd>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg transition-colors"
              style={{ 
                backgroundColor: 'var(--bg)',
                color: 'var(--text)'
              }}
            >
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {user && (
              <>
                {/* Notifications */}
                <Link
                  href="/settings"
                  className="p-2 rounded-lg transition-colors relative"
                  style={{ 
                    backgroundColor: 'var(--bg)',
                    color: 'var(--text)'
                  }}
                >
                  <Bell size={16} />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </Link>

                {/* Settings */}
                <Link
                  href="/settings"
                  className="p-2 rounded-lg transition-colors"
                  style={{ 
                    backgroundColor: 'var(--bg)',
                    color: 'var(--text)'
                  }}
                >
                  <Settings size={16} />
                </Link>

                {/* User Menu */}
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 p-2 rounded-lg transition-colors"
                    style={{ 
                      backgroundColor: 'var(--bg)',
                      color: 'var(--text)'
                    }}
                  >
                    {user.photoURL ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
            <img 
                        src={user.photoURL} 
                        alt="Profile" 
                        className="w-6 h-6 rounded-full"
                      />
                    ) : (
                      <User size={16} />
                    )}
                    <span className="text-sm hidden md:block">
                      {user.displayName || user.email?.split('@')[0]}
                    </span>
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg border z-50"
                         style={{ 
                           backgroundColor: 'var(--surface)',
                           borderColor: 'var(--border)'
                         }}>
                      <div className="p-2">
                        <button
                          onClick={handleSignOut}
                          className="w-full text-left px-3 py-2 rounded text-sm transition-colors"
                          style={{ 
                            color: 'var(--text)',
                            backgroundColor: 'transparent'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = 'var(--bg)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }}
                        >
                          Sign Out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {!user && (
              <Link 
                href="/login"
                className="px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
                style={{
                  backgroundColor: 'var(--accent)',
                  color: 'var(--accent-contrast)'
                }}
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
