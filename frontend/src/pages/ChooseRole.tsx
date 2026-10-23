import { Link, useNavigate } from "react-router-dom"
import TopNav from "@/components/TopNav"
import { useRole, type UserRole } from "@/lib/role"
import { ArrowLeft, Check, Building2, User } from "lucide-react"
import "./LandingPage.css"
import "./ChooseRole.css"

export default function ChooseRole() {
  const { setRole } = useRole()
  const navigate = useNavigate()

  const handleSelectRole = (role: UserRole) => {
    setRole(role)
    if (role === "company") {
      navigate("/overview")
    } else {
      navigate("/submit")
    }
  }

  return (
    <div className="landing-page choose-role-page">
      {/* TopNav Component - renders logo only on /choose-role */}
      <TopNav />

      {/* Shared Gradient Background Matching Landing Page Exactly */}
      <div className="landing-bg-container" aria-hidden="true">
        <div className="landing-hero-gradient" />
        <div className="landing-background-shape">
          <svg
            viewBox="0 0 1440 850"
            fill="none"
            preserveAspectRatio="xMidYMid meet"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g
              filter="url(#heroBackgroundShapeFilterChooseRole)"
              style={{ mixBlendMode: "plus-lighter" }}
            >
              <path
                d="M774.33 0C774.33 456.393 1186.78 682.164 1393 738H47C253.223 682.164 665.67 456.393 665.67 0H774.33Z"
                fill="url(#heroBackgroundShapeGradientChooseRole)"
                fillOpacity="0.12"
              />
            </g>
            <defs>
              <filter
                id="heroBackgroundShapeFilterChooseRole"
                x="-65"
                y="-112"
                width="1570"
                height="962"
                filterUnits="userSpaceOnUse"
                colorInterpolationFilters="sRGB"
              >
                <feFlood floodOpacity="0" result="BackgroundImageFix" />
                <feBlend
                  mode="normal"
                  in="SourceGraphic"
                  in2="BackgroundImageFix"
                  result="shape"
                />
                <feGaussianBlur
                  stdDeviation="56"
                  result="effect1_foregroundBlur"
                />
              </filter>
              <linearGradient
                id="heroBackgroundShapeGradientChooseRole"
                x1="232.075"
                y1="100.869"
                x2="232.075"
                y2="735.916"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#4D90FD" stopOpacity="0" />
                <stop offset="0.25" stopColor="#4D90FD" />
                <stop offset="0.509615" stopColor="#76D0F4" />
                <stop offset="0.759615" stopColor="#FF2C2C" />
                <stop offset="1" stopColor="#FFE4D7" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Main Single Viewport Container */}
      <main className="choose-role-main">
        {/* Centered Heading & Subtitle */}
        <div className="choose-role-header">
          <h1 className="choose-role-title">Who are you signing in as?</h1>
          <p className="choose-role-subtitle">
            Choose your portal role to access privacy-preserving intelligence tools.
          </p>
        </div>

        {/* Two Glass Cards Side by Side */}
        <div className="choose-role-cards">
          {/* Card 1: Company */}
          <div
            role="button"
            tabIndex={0}
            className="choose-role-card"
            onClick={() => handleSelectRole("company")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                handleSelectRole("company")
              }
            }}
            aria-label="Continue as Company: Review and resolve customer complaints"
          >
            <div className="choose-role-card-top">
              <div className="choose-role-icon-box">
                <Building2 className="w-5 h-5 text-[#52aeff]" aria-hidden="true" />
              </div>
              <h2 className="choose-role-card-title">Company</h2>
              <p className="choose-role-card-tagline">
                Review and resolve customer complaints
              </p>
              <ul className="choose-role-capabilities" aria-label="Company capabilities">
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Executive Overview & Trends</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Human Review Queue</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Root Cause Analysis</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Automated Surge Alerts</span>
                </li>
              </ul>
            </div>
            <button type="button" tabIndex={-1} className="landing-btn choose-role-btn">
              Continue as Company
            </button>
          </div>

          {/* Card 2: Customer */}
          <div
            role="button"
            tabIndex={0}
            className="choose-role-card"
            onClick={() => handleSelectRole("customer")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                handleSelectRole("customer")
              }
            }}
            aria-label="Continue as Customer: Raise a complaint and track its progress"
          >
            <div className="choose-role-card-top">
              <div className="choose-role-icon-box" style={{ background: "rgba(118, 208, 244, 0.12)", borderColor: "rgba(118, 208, 244, 0.25)", color: "#76D0F4" }}>
                <User className="w-5 h-5 text-[#76D0F4]" aria-hidden="true" />
              </div>
              <h2 className="choose-role-card-title">Customer</h2>
              <p className="choose-role-card-tagline">
                Raise a complaint and track its progress
              </p>
              <ul className="choose-role-capabilities" aria-label="Customer capabilities">
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Submit Complaint with PII Redaction</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Real-Time Status Tracking</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>Zero-Trust Privacy Safeguards</span>
                </li>
                <li className="choose-role-capability-item">
                  <Check className="choose-role-check-icon" aria-hidden="true" />
                  <span>AI-Powered Complaint Summary</span>
                </li>
              </ul>
            </div>
            <button type="button" tabIndex={-1} className="landing-btn choose-role-btn">
              Continue as Customer
            </button>
          </div>
        </div>

        {/* Back Link */}
        <Link to="/" className="choose-role-back">
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Back to home</span>
        </Link>
      </main>
    </div>
  )
}
