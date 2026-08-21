"use client";

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sun, Moon, Bell, User } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { user, signOut } = useAuth();
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);

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

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-6">
            <Link 
              href="/" 
              className="text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: 'var(--text)' }}
            >
              Home
            </Link>
            {user && (
              <>
                <Link 
                  href="/dashboard" 
                  className="text-sm font-medium transition-colors hover:opacity-80"
                  style={{ color: 'var(--text)' }}
                >
                  Dashboard
                </Link>
                <Link 
                  href="/analyze" 
                  className="text-sm font-medium transition-colors hover:opacity-80"
                  style={{ color: 'var(--text)' }}
                >
                  Analyze
                </Link>
              </>
            )}
          </div>

          {/* Right side - Theme toggle, notifications, user menu */}
          <div className="flex items-center gap-3">
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
                <button className="p-2 rounded-lg transition-colors relative"
                        style={{ 
                          backgroundColor: 'var(--bg)',
                          color: 'var(--text)'
                        }}>
                  <Bell size={16} />
                  {/* Notification badge - will be implemented later */}
                </button>

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
