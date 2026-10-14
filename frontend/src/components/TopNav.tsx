import React, { useState, useEffect } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import {
  LayoutDashboard,
  Send,
  ShieldCheck,
  Network,
  Inbox,
  ChevronRight,
} from "lucide-react"
import "./TopNav.css"

export interface NavItem {
  label: string
  path: string
  icon: React.ElementType
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", path: "/overview", icon: LayoutDashboard },
  { label: "Submit Complaint", path: "/submit", icon: Send },
  { label: "Privacy", path: "/privacy", icon: ShieldCheck },
  { label: "Root Causes", path: "/root-causes", icon: Network },
  { label: "Review Queue", path: "/review", icon: Inbox },
]

interface TopNavProps {
  scrollProgress?: number
  rightControls?: React.ReactNode
}

export default function TopNav({ scrollProgress, rightControls }: TopNavProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const isLanding = location.pathname === "/"

  const [scrolled, setScrolled] = useState(!isLanding)
  const [mobileOpen, setMobileOpen] = useState(false)

  // Track scroll position on landing page
  useEffect(() => {
    if (!isLanding) {
      setScrolled(true)
      return
    }

    const handleScroll = () => {
      setScrolled(window.scrollY > 40)
    }

    handleScroll()
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [isLanding])

  // Close mobile sheet on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  // Lock body scroll while mobile sheet is open
  useEffect(() => {
    if (mobileOpen) {
      const origOverflow = document.body.style.overflow
      document.body.style.overflow = "hidden"
      return () => {
        document.body.style.overflow = origOverflow
      }
    }
  }, [mobileOpen])

  const handleGetStarted = (e: React.MouseEvent) => {
    e.preventDefault()
    setMobileOpen(false)
    navigate("/overview")
  }

  const isSolid = !isLanding || scrolled

  return (
    <header
      className={`top-nav-wrapper ${isSolid ? "is-solid" : "is-landing-top"} ${
        isLanding ? "is-landing" : ""
      }`}
    >
      {/* Scroll progress indicator for landing page */}
      {isLanding && scrollProgress !== undefined && scrollProgress > 0 && (
        <div
          className="top-nav-scroll-progress"
          style={{ width: `${Math.min(100, Math.max(0, scrollProgress))}%` }}
          aria-hidden="true"
        />
      )}

      <div className="top-nav-inner">
        {/* Left: Logo + Wordmark */}
        <Link
          to="/"
          className="top-nav-logo"
          aria-label="PII Complaint Intelligence Platform home"
        >
          <div className="top-nav-logo-mark">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 2L3 6V11.5C3 16.75 6.84 21.6 12 22.8C17.16 21.6 21 16.75 21 11.5V6L12 2Z"
                fill="#3b82f6"
                fillOpacity="0.25"
                stroke="#60a0ff"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="12" cy="11" r="2.2" fill="currentColor" />
              <path
                d="M12 13.2V15.8"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <span className="top-nav-logo-text">PII Complaint Intelligence</span>
        </Link>

        {/* Center: Desktop Navigation Links */}
        <nav className="top-nav-links" aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path))
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`top-nav-item ${isActive ? "is-active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Right: Actions / Controls */}
        <div className="top-nav-right">
          {isLanding ? (
            <Link
              to="/overview"
              className="top-nav-cta"
              onClick={handleGetStarted}
            >
              <span>Get Started</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  d="M9 6L15 12L9 18"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Link>
          ) : (
            rightControls
          )}

          {/* Mobile hamburger toggle */}
          <button
            type="button"
            className="top-nav-menu-toggle"
            aria-label="Open navigation menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(true)}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M4 7H16" strokeLinecap="round" />
              <path d="M4 13H16" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Navigation Sheet */}
      {mobileOpen && (
        <div
          className="top-nav-mobile-sheet"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile Navigation"
        >
          <div>
            <div className="top-nav-mobile-topbar">
              <div className="top-nav-logo">
                <div className="top-nav-logo-mark">
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M12 2L3 6V11.5C3 16.75 6.84 21.6 12 22.8C17.16 21.6 21 16.75 21 11.5V6L12 2Z"
                      fill="#3b82f6"
                      fillOpacity="0.25"
                      stroke="#60a0ff"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <circle cx="12" cy="11" r="2.2" fill="#ffffff" />
                    <path
                      d="M12 13.2V15.8"
                      stroke="#ffffff"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <span className="top-nav-logo-text" style={{ color: "#ffffff" }}>
                  PII Complaint Intelligence
                </span>
              </div>
              <button
                type="button"
                className="top-nav-mobile-close"
                aria-label="Close navigation menu"
                onClick={() => setMobileOpen(false)}
              >
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    d="M18 6L6 18M6 6l12 12"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>

            <p className="top-nav-mobile-eyebrow">Navigation</p>
            <nav className="top-nav-mobile-links" aria-label="Mobile menu navigation">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon
                const isActive =
                  location.pathname === item.path ||
                  (item.path !== "/" && location.pathname.startsWith(item.path))
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`top-nav-mobile-link ${isActive ? "is-active" : ""}`}
                    aria-current={isActive ? "page" : undefined}
                    onClick={() => setMobileOpen(false)}
                  >
                    <span className="flex items-center gap-3">
                      <Icon className="w-5 h-5 opacity-70" />
                      {item.label}
                    </span>
                    <ChevronRight className="w-4 h-4 opacity-40" />
                  </Link>
                )
              })}
            </nav>

            <div className="top-nav-mobile-divider" aria-hidden="true" />

            {isLanding ? (
              <Link
                to="/overview"
                className="top-nav-mobile-action"
                onClick={handleGetStarted}
              >
                Get Started
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    d="M9 6L15 12L9 18"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </Link>
            ) : (
              <div className="top-nav-mobile-controls">
                <span className="text-xs text-white/60">System Controls</span>
                <div className="flex items-center gap-3">{rightControls}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
