import React, { useState, useEffect, useRef } from "react"
import { Link, useNavigate } from "react-router-dom"
import TopNav from "@/components/TopNav"
import {
  ShieldCheck,
  Cpu,
  BarChart3,
  Network,
  Scale,
  FileText,
  Lock,
  GitBranch,
  Layers,
} from "lucide-react"
import "./LandingPage.css"

const TECH_STACK = [
  "Microsoft Presidio",
  "FastAPI",
  "DistilBERT",
  "Sentence-BERT",
  "FAISS",
  "React 19",
  "Tailwind CSS",
]

// Word-reveal sentence based strictly on project README
const REVEAL_STATEMENT =
  "An enterprise NLP platform that redacts personally identifiable information from consumer financial complaints before downstream analysis happens, surfacing operational intelligence without exposing sensitive customer data."

const REVEAL_WORDS = REVEAL_STATEMENT.split(" ")

// 5 Feature cards matching real project pages and capabilities
const FEATURE_CARDS = [
  {
    path: "/overview",
    badge: "CFPB DOMAINS",
    title: "Executive Intelligence",
    description:
      "Real-time analytics across 9 consolidated financial domains, volume trajectories, and automated triage surges.",
    icon: BarChart3,
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-end p-2 gap-1.5">
        <div className="flex items-center justify-between text-[10px] text-white/50 mb-1">
          <span>Credit Reporting</span>
          <span className="text-[#52aeff] font-mono">1,120</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
          <div className="bg-[#52aeff] h-full rounded-full w-[82%]" />
        </div>
        <div className="flex items-center justify-between text-[10px] text-white/50 mb-1">
          <span>Debt Collection</span>
          <span className="text-[#76D0F4] font-mono">842</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
          <div className="bg-[#76D0F4] h-full rounded-full w-[64%]" />
        </div>
        <div className="flex items-center justify-between text-[10px] text-white/50 mb-1">
          <span>Credit Card</span>
          <span className="text-[#badfff] font-mono">512</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
          <div className="bg-[#badfff] h-full rounded-full w-[42%]" />
        </div>
      </div>
    ),
  },
  {
    path: "/submit",
    badge: "100% RECALL",
    title: "Presidio Privacy Scrubbing",
    description:
      "Dual-engine NER and custom regex recognizers for account numbers, Aadhaar, credit cards, and credential strings.",
    icon: ShieldCheck,
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-center p-3 gap-2 font-mono text-xs">
        <div className="flex items-center gap-1.5 text-white/40 text-[10px]">
          <Lock className="w-3 h-3 text-[#52aeff]" />
          <span>INCOMING NARRATIVE STREAM</span>
        </div>
        <div className="bg-black/40 rounded p-2 text-white/70 text-[11px] leading-relaxed border border-white/5">
          <span>My account </span>
          <span className="bg-[#52aeff]/20 text-[#52aeff] px-1 py-0.5 rounded border border-[#52aeff]/30">
            [ACCOUNT_NUMBER]
          </span>
          <span> was billed. SSN </span>
          <span className="bg-emerald-500/20 text-emerald-400 px-1 py-0.5 rounded border border-emerald-500/30">
            [SSN_REDACTED]
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>0 Entity Leaks Detected (F1: 97.67%)</span>
        </div>
      </div>
    ),
  },
  {
    path: "/privacy",
    badge: "k-ANONYMITY",
    title: "Quasi-Identifier Mitigation",
    description:
      "Audit record-level re-identification risk with quarter-binning mitigation achieving a 37.3% risk reduction.",
    icon: Scale,
    renderVisual: () => (
      <div className="w-full h-full flex items-center justify-center p-2 gap-4">
        <div className="relative flex items-center justify-center">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              cx="48"
              cy="48"
              r="38"
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="6"
              fill="transparent"
            />
            <circle
              cx="48"
              cy="48"
              r="38"
              stroke="#52aeff"
              strokeWidth="6"
              fill="transparent"
              strokeDasharray="238"
              strokeDashoffset="75"
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-sm font-bold text-white font-mono">-37.3%</span>
            <span className="text-[9px] text-white/50">Risk Delta</span>
          </div>
        </div>
        <div className="flex flex-col gap-1 text-[11px]">
          <div className="text-white/60">
            Baseline: <span className="text-rose-400 font-mono">82.0%</span>
          </div>
          <div className="text-white/60">
            Mitigated: <span className="text-emerald-400 font-mono">44.7%</span>
          </div>
          <div className="text-[10px] text-white/40 mt-1">k &lt; 5 Re-ID Threshold</div>
        </div>
      </div>
    ),
  },
  {
    path: "/root-causes",
    badge: "NETWORK AI",
    title: "Causal Graph Network",
    description:
      "Clustered semantic cause-and-effect network ranking systemic corporate drivers behind recurring customer grievances.",
    icon: Network,
    renderVisual: () => (
      <div className="w-full h-full relative flex items-center justify-center">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(82,174,255,0.12)_0%,transparent_70%)]" />
        <svg className="w-full h-full p-2" viewBox="0 0 200 120">
          <line x1="30" y1="60" x2="100" y2="30" stroke="rgba(82,174,255,0.4)" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="30" y1="60" x2="100" y2="90" stroke="rgba(82,174,255,0.4)" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="100" y1="30" x2="170" y2="60" stroke="#52aeff" strokeWidth="2" />
          <line x1="100" y1="90" x2="170" y2="60" stroke="#76D0F4" strokeWidth="2" />
          <circle cx="30" cy="60" r="8" fill="#010918" stroke="#52aeff" strokeWidth="2" />
          <circle cx="100" cy="30" r="10" fill="#002869" stroke="#76D0F4" strokeWidth="2" />
          <circle cx="100" cy="90" r="9" fill="#002869" stroke="#badfff" strokeWidth="2" />
          <circle cx="170" cy="60" r="12" fill="#0056ec" stroke="#ffffff" strokeWidth="2" />
          <text x="170" y="64" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="bold">ROOT</text>
        </svg>
      </div>
    ),
  },
  {
    path: "/review",
    badge: "TRIAGE ENGINE",
    title: "Multi-Model Consensus",
    description:
      "Consensus engine flagging divergent predictions across SVM, Sentence-BERT, and DistilBERT for human operator audit.",
    icon: Cpu,
    renderVisual: () => (
      <div className="w-full h-full flex flex-col justify-center p-3 gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-white/60">TF-IDF + Linear SVM</span>
          <span className="text-emerald-400 font-mono text-[11px]">74.4% F1</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-white/60">SBERT + Logistic Reg</span>
          <span className="text-emerald-400 font-mono text-[11px]">74.7% F1</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-white/60">DistilBERT Transformer</span>
          <span className="text-[#52aeff] font-mono text-[11px]">Consensus</span>
        </div>
        <div className="mt-1 pt-1 border-t border-white/10 flex items-center justify-between text-[10px] text-amber-400/90">
          <span>Review Threshold: &lt; 0.40</span>
          <span className="bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/20">Auto Flag</span>
        </div>
      </div>
    ),
  },
]

// 4 Steps for "How it works"
const HOW_IT_WORKS_STEPS = [
  {
    num: "STEP 01",
    title: "Raw Narrative Ingestion",
    description:
      "Consumer submits raw complaint text containing unstructured sensitive financial identifiers and distress narratives.",
    icon: FileText,
  },
  {
    num: "STEP 02",
    title: "Dual-Layer Presidio Scrubbing",
    description:
      "Microsoft Presidio NER combined with custom pattern recognizers masks account numbers, Aadhaar, cards, and credentials with zero PII leaks.",
    icon: ShieldCheck,
  },
  {
    num: "STEP 03",
    title: "3-Model Consensus Evaluation",
    description:
      "TF-IDF+Linear SVM, Sentence-BERT, and fine-tuned DistilBERT classify the redacted complaint concurrently; disagreements trigger triage review.",
    icon: Layers,
  },
  {
    num: "STEP 04",
    title: "Hierarchical Triage & Root Causes",
    description:
      "Granular sub-issue classifiers, FAISS duplicate detection, and causal graph clustering surface systemic banking insights.",
    icon: GitBranch,
  },
]

export default function LandingPage() {
  const navigate = useNavigate()

  // Scroll states for scroll-driven animations
  const [scrollProgress, setScrollProgress] = useState(0)
  const [heroScale, setHeroScale] = useState(1)
  const [heroOpacity, setHeroOpacity] = useState(1)
  const [heroParallaxY, setHeroParallaxY] = useState(0)

  // Moment B: Word reveal progress
  const [litWordCount, setLitWordCount] = useState(0)

  // Moment C: Horizontal feature track progress
  const [featureTrackX, setFeatureTrackX] = useState(0)
  const [featureTrackPct, setFeatureTrackPct] = useState(0)

  // Moment D: SVG line progress
  const [pipelineProgress, setPipelineProgress] = useState(0)

  // Section Refs
  const heroRef = useRef<HTMLDivElement>(null)
  const wordRevealRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)
  const pipelineRef = useRef<HTMLDivElement>(null)

  // RequestAnimationFrame scroll loop
  useEffect(() => {
    let rAF = 0

    const updateScrollMetrics = () => {
      const scrollY = window.scrollY
      const docHeight = document.documentElement.scrollHeight
      const winHeight = window.innerHeight

      // 1. Overall scroll progress (for TopNav progress line)
      const totalScrollable = docHeight - winHeight
      const overallPct = totalScrollable > 0 ? (scrollY / totalScrollable) * 100 : 0
      setScrollProgress(overallPct)

      // 2. Hero exit (Moment A): scales down slightly and fades over the first 600px
      if (scrollY <= 650) {
        const exitProgress = Math.min(1, Math.max(0, scrollY / 600))
        setHeroScale(1 - exitProgress * 0.06) // 1 -> 0.94
        setHeroOpacity(Math.max(0, 1 - exitProgress * 1.15)) // 1 -> 0
        setHeroParallaxY(scrollY * 0.2)
      } else {
        setHeroOpacity(0)
      }

      // 3. Pinned Word Reveal (Moment B)
      if (wordRevealRef.current) {
        const rect = wordRevealRef.current.getBoundingClientRect()
        const trackHeight = wordRevealRef.current.offsetHeight - winHeight
        if (trackHeight > 0) {
          const progress = Math.min(1, Math.max(0, -rect.top / trackHeight))
          const count = Math.round(progress * REVEAL_WORDS.length)
          setLitWordCount(count)
        }
      }

      // 4. Horizontal Feature Track (Moment C)
      if (featuresRef.current) {
        const rect = featuresRef.current.getBoundingClientRect()
        const trackHeight = featuresRef.current.offsetHeight - winHeight
        if (trackHeight > 0 && window.innerWidth > 860) {
          const progress = Math.min(1, Math.max(0, -rect.top / trackHeight))
          setFeatureTrackPct(progress * 100)
          // Total horizontal scroll distance ~ (card width 360 + gap 24) * 4 = 1536px
          const maxScroll = Math.max(0, (FEATURE_CARDS.length - 1) * 384)
          setFeatureTrackX(progress * maxScroll)
        }
      }

      // 5. How It Works Pipeline (Moment D)
      if (pipelineRef.current) {
        const rect = pipelineRef.current.getBoundingClientRect()
        const enterPoint = winHeight * 0.75
        const exitPoint = -rect.height * 0.25
        const totalDistance = enterPoint - exitPoint
        const currentDistance = enterPoint - rect.top
        const progress = Math.min(1, Math.max(0, currentDistance / totalDistance))
        setPipelineProgress(progress)
      }
    }

    const onScroll = () => {
      cancelAnimationFrame(rAF)
      rAF = requestAnimationFrame(updateScrollMetrics)
    }

    window.addEventListener("scroll", onScroll, { passive: true })
    updateScrollMetrics()

    return () => {
      cancelAnimationFrame(rAF)
      window.removeEventListener("scroll", onScroll)
    }
  }, [])

  const handleGetStarted = (e: React.MouseEvent) => {
    e.preventDefault()
    navigate("/overview")
  }

  return (
    <div className="landing-page">
      {/* Shared TopNav across both landing and dashboard */}
      <TopNav scrollProgress={scrollProgress} />

      {/* Fixed Steady Background Gradient for the Entire Landing Page */}
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
              filter="url(#heroBackgroundShapeFilter)"
              style={{ mixBlendMode: "plus-lighter" }}
            >
              <path
                d="M774.33 0C774.33 456.393 1186.78 682.164 1393 738H47C253.223 682.164 665.67 456.393 665.67 0H774.33Z"
                fill="url(#heroBackgroundShapeGradient)"
                fillOpacity="0.12"
              />
            </g>
            <defs>
              <filter
                id="heroBackgroundShapeFilter"
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
                id="heroBackgroundShapeGradient"
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

      {/* =========================================================
          SECTION A: HERO SECTION (Unchanged First Screen at Scroll 0)
          ========================================================= */}
      <div className="landing-hero-screen" ref={heroRef}>
        {/* Hero Center Section with Exit Fade/Scale */}
        <main
          className="landing-hero-content"
          id="main-content"
          style={{
            transform: `scale(${heroScale}) translateY(${heroParallaxY}px)`,
            opacity: heroOpacity,
          }}
        >
          {/* Announcement Pill */}
          <Link to="/overview" className="landing-pill" onClick={handleGetStarted}>
            <span className="landing-pill-label">
              Zero PII Leaks · 100% Redaction Recall
            </span>
            <span className="landing-pill-divider" aria-hidden="true" />
            <span className="landing-pill-link">
              Explore Platform
              <span aria-hidden="true">→</span>
            </span>
          </Link>

          {/* Two-Line Headline */}
          <h1 className="landing-headline">
            <span className="landing-headline-line primary">
              Protect consumer privacy.
            </span>
            <span className="landing-headline-line secondary">
              Uncover complaint intelligence.
            </span>
          </h1>

          {/* One-Line Subtext */}
          <p className="landing-subtitle">
            Enterprise NLP that automatically redacts sensitive PII before
            analysis, classifying domains and surfacing systemic root causes
            while guaranteeing complete privacy.
          </p>

          {/* CTA Button */}
          <div className="landing-cta-slot">
            <button
              type="button"
              className="landing-btn"
              onClick={handleGetStarted}
            >
              Get Started
            </button>
          </div>
        </main>

        {/* Quiet Bottom Row */}
        <footer
          className="landing-bottom-row"
          aria-label="Built with technologies"
        >
          <span className="landing-bottom-caption">Built with</span>
          <div className="landing-bottom-chips">
            {TECH_STACK.map((tech) => (
              <span key={tech} className="landing-tech-chip">
                {tech}
              </span>
            ))}
          </div>
        </footer>
      </div>

      {/* =========================================================
          SECTION B: PINNED WORD-REVEAL STATEMENT
          ========================================================= */}
      <section
        className="landing-word-reveal-track"
        ref={wordRevealRef}
        aria-label="Platform Mission Statement"
      >
        <div className="landing-word-reveal-sticky">
          <div className="landing-word-reveal-inner">
            <span className="landing-word-reveal-tag">
              Privacy-by-Design Architecture
            </span>
            <p className="landing-word-reveal-text">
              {REVEAL_WORDS.map((word, index) => {
                const isLit = index < litWordCount
                return (
                  <span
                    key={index}
                    className="landing-word-reveal-word"
                    style={{
                      opacity: isLit ? 1 : 0.30,
                      color: isLit ? "#ffffff" : "#badfff",
                      textShadow: isLit
                        ? "0 0 20px rgba(82, 174, 255, 0.4)"
                        : "none",
                    }}
                  >
                    {word}
                  </span>
                )
              })}
            </p>
          </div>
        </div>
      </section>

      {/* =========================================================
          SECTION C: PINNED HORIZONTAL FEATURE TRACK
          ========================================================= */}
      <section
        className="landing-features-track"
        ref={featuresRef}
        aria-label="Core Capabilities"
      >
        <div className="landing-features-sticky">
          <div className="landing-features-header">
            <div className="landing-features-eyebrow">Enterprise Modules</div>
            <h2 className="landing-features-title">
              Built for precision triage & compliance
            </h2>
          </div>

          <div className="landing-features-viewport">
            <div
              className="landing-features-row"
              style={{
                transform: `translateX(-${featureTrackX}px)`,
              }}
            >
              {FEATURE_CARDS.map((card) => {
                const Icon = card.icon
                return (
                  <div key={card.path} className="landing-feature-card">
                    <div className="landing-feature-card-top">
                      <div className="flex items-center justify-between">
                        <span className="landing-feature-badge">
                          {card.badge}
                        </span>
                        <Icon className="w-5 h-5 text-[#52aeff] opacity-75" />
                      </div>
                      <h3 className="landing-feature-card-title">{card.title}</h3>
                      <p className="landing-feature-card-desc">
                        {card.description}
                      </p>
                    </div>

                    <div className="landing-feature-visual">
                      {card.renderVisual()}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Progress Indicator Under Track */}
          <div className="landing-features-progress-bar" aria-hidden="true">
            <div
              className="landing-features-progress-fill"
              style={{ width: `${Math.min(100, Math.max(0, featureTrackPct))}%` }}
            />
          </div>
        </div>
      </section>

      {/* =========================================================
          SECTION D: "HOW IT WORKS" FLOW WITH DRAWING SVG LINE
          ========================================================= */}
      <section
        className="landing-pipeline-section"
        ref={pipelineRef}
        aria-label="How the Platform Works"
      >
        <div className="landing-pipeline-header">
          <div className="landing-pipeline-eyebrow">Pipeline Flow</div>
          <h2 className="landing-pipeline-title">From Raw Text to Secure Intelligence</h2>
        </div>

        <div className="landing-pipeline-container">
          {/* Scroll-linked vertical drawing line */}
          <svg className="landing-pipeline-svg-line" aria-hidden="true">
            <line
              x1="1"
              y1="0"
              x2="1"
              y2="100%"
              stroke="rgba(82, 174, 255, 0.2)"
              strokeWidth="2"
            />
            <line
              x1="1"
              y1="0"
              x2="1"
              y2="100%"
              stroke="#52aeff"
              strokeWidth="2"
              strokeDasharray="600"
              strokeDashoffset={Math.max(0, 600 * (1 - pipelineProgress * 1.3))}
              strokeLinecap="round"
            />
          </svg>

          {HOW_IT_WORKS_STEPS.map((step, idx) => {
            const Icon = step.icon
            // Step lights up progressively as line reaches it
            const threshold = idx / (HOW_IT_WORKS_STEPS.length - 1) * 0.75
            const isActive = pipelineProgress >= threshold
            return (
              <div
                key={step.num}
                className={`landing-pipeline-step ${isActive ? "is-active" : ""}`}
              >
                <div className="landing-pipeline-step-node">
                  <Icon className="w-6 h-6" />
                </div>
                <div className="landing-pipeline-step-card">
                  <div className="landing-pipeline-step-num">{step.num}</div>
                  <h3 className="landing-pipeline-step-title">{step.title}</h3>
                  <p className="landing-pipeline-step-desc">{step.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* =========================================================
          SECTION E: CLOSING SECTION WITH CTA
          ========================================================= */}
      <section className="landing-closing-section">
        <div className="landing-closing-glow" aria-hidden="true" />
        <div className="landing-closing-content">
          <h2 className="landing-closing-headline">
            Ready to inspect the intelligence platform?
          </h2>
          <p className="landing-closing-subtitle">
            Explore live anonymized complaints, model consensus benchmarks, and
            causal root-cause graphs.
          </p>
          <button
            type="button"
            className="landing-btn"
            onClick={handleGetStarted}
          >
            Get Started
          </button>
        </div>
      </section>
    </div>
  )
}
