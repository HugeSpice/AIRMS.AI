import React, { useState, useEffect, useMemo } from 'react';
import Hyperspeed from './Hyperspeed';
import Pricing from '@/components/ui/genz-pricing';
import './App.css';

interface AppProps {
  navigate?: (page: string) => void;
}

const App: React.FC<AppProps> = ({ navigate }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  
  const [activeNavItem, setActiveNavItem] = useState('home');



  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    // Check current URL to set active nav item
    const checkCurrentPage = () => {
      const hash = window.location.hash;
      
      if (hash === '#docs') {
        setActiveNavItem('docs');
      } else if (hash === '#home' || hash === '#hero') {
        setActiveNavItem('home');
      } else if (hash === '#features') {
        setActiveNavItem('features');
      } else if (hash === '#testimonials') {
        setActiveNavItem('testimonials');
      } else if (hash === '#pricing') {
        setActiveNavItem('pricing');
      } else if (hash === '#contact') {
        setActiveNavItem('contact');
      } else if (hash === '' || hash === '#') {
        setActiveNavItem('home');
      } else {
        setActiveNavItem('home');
      }
    };

    // Check on mount
    checkCurrentPage();

    // Listen for hash changes
    const handleHashChange = () => {
      checkCurrentPage();
    };

    // Intersection Observer for scroll-based highlighting
    const observerOptions = {
      root: null,
      rootMargin: '-20% 0px -70% 0px',
      threshold: 0
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const sectionId = entry.target.id;
          
          if (sectionId === 'hero') {
            setActiveNavItem('home');
          } else if (sectionId === 'features') {
            setActiveNavItem('features');
          } else if (sectionId === 'testimonials') {
            setActiveNavItem('testimonials');
          } else if (sectionId === 'pricing') {
            setActiveNavItem('pricing');
          } else if (sectionId === 'contact') {
            setActiveNavItem('contact');
          }
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    // Observe all sections
    const sections = ['hero', 'features', 'testimonials', 'pricing', 'contact'];
    sections.forEach(sectionId => {
      const element = document.getElementById(sectionId);
      if (element) {
        observer.observe(element);
      }
    });

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('hashchange', handleHashChange);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('hashchange', handleHashChange);
      observer.disconnect();
    };
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMenuOpen(false);
      // Don't automatically set active nav item here - let the click handlers do it
    }
  };



  // Testimonials data
  const testimonials = [
    {
      quote: "SecureFlow saved us months of security implementation. The PII detection is incredibly accurate, and the API integration was seamless. Our compliance team loves the audit trails.",
      name: "Alex Chen",
      role: "CTO, FinTech Startup",
      avatar: "👨‍💻"
    },
    {
      quote: "The hallucination detection has been a game-changer for our AI-powered customer support. We've reduced false information by 95% and our customer satisfaction scores improved dramatically.",
      name: "Sarah Johnson", 
      role: "Head of AI, E-commerce Platform",
      avatar: "👩‍💼"
    },
    {
      quote: "Enterprise-grade security with developer-friendly APIs. AIRMS handles all our compliance requirements while our team focuses on building great products.",
      name: "Marcus Rodriguez",
      role: "VP Engineering, Healthcare Tech", 
      avatar: "DS"
    },
    {
      quote: "The adversarial attack detection caught prompt injections we didn't even know were possible. SecureFlow's security expertise is unmatched.",
      name: "Dr. Emily Watson",
      role: "Security Researcher, AI Lab",
      avatar: "👩‍🔬"
    }
  ];





  const [currentTestimonial, setCurrentTestimonial] = useState(0);

  // Auto-rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000); // Change every 5 seconds
    
    return () => clearInterval(interval);
  }, [testimonials.length]);



  // Functions for manual navigation
  const nextTestimonial = () => {
    setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    setCurrentTestimonial((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  const goToTestimonial = (index: number) => {
    setCurrentTestimonial(index);
  };





  // Memoize the Hyperspeed options to prevent re-rendering
  const hyperspeedOptions = useMemo(() => ({
    distortion: 'xyDistortion',
    length: 400,
    roadWidth: 18,
    islandWidth: 2,
    lanesPerRoad: 3,
    fov: 90,
    fovSpeedUp: 150,
    speedUp: 1.2,
    carLightsFade: 0.4,
    totalSideLightSticks: 50,
    lightPairsPerRoadWay: 50,
    shoulderLinesWidthPercentage: 0.05,
    brokenLinesWidthPercentage: 0.1,
    brokenLinesLengthPercentage: 0.5,
    lightStickWidth: [0.12, 0.5] as [number, number],
    lightStickHeight: [1.3, 1.7] as [number, number],
    movingAwaySpeed: [35, 50] as [number, number],
    movingCloserSpeed: [-70, -95] as [number, number],
    carLightsLength: [400 * 0.05, 400 * 0.15] as [number, number],
    carLightsRadius: [0.05, 0.14] as [number, number],
    carWidthPercentage: [0.3, 0.5] as [number, number],
    carShiftX: [-0.2, 0.2] as [number, number],
    carFloorSeparation: [0.05, 1] as [number, number],
    colors: {
      roadColor: 0x010101,
      islandColor: 0x424242,
      background: 0x000000,
      shoulderLines: 0x9e9e9e,
      brokenLines: 0x9e9e9e,
      leftCars: [0xe394f3, 0x6c44a1, 0xb01c1c],
      rightCars: [0xfc544a, 0xfdfdfd, 0x9e9e9e],
      sticks: 0xe394f3,
    }
  }), []);

  return (
    <div className="app">
      {/* Navigation */}
      <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
        <div className="nav-container">
          <div className="nav-logo">

            <span className="logo-text">AIRMS</span>
          </div>
          
          <div className={`nav-menu ${isMenuOpen ? 'active' : ''}`}>
            <button 
              className={`nav-item ${activeNavItem === 'home' ? 'active' : ''}`} 
              onClick={() => {
                scrollToSection('hero');
                setActiveNavItem('home');
              }}
            >
              Home
            </button>
            <button 
              className={`nav-item ${activeNavItem === 'features' ? 'active' : ''}`}
              onClick={() => {
                scrollToSection('features');
                setActiveNavItem('features');
              }}
            >
              Features
            </button>

            <button 
              className={`nav-item ${activeNavItem === 'testimonials' ? 'active' : ''}`}
              onClick={() => {
                scrollToSection('testimonials');
                setActiveNavItem('testimonials');
              }}
            >
              Reviews
            </button>
            <button 
              className={`nav-item ${activeNavItem === 'pricing' ? 'active' : ''}`}
              onClick={() => {
                scrollToSection('pricing');
                setActiveNavItem('pricing');
              }}
            >
              Pricing
            </button>
            <button 
              className={`nav-item ${activeNavItem === 'docs' ? 'active' : ''}`}
              onClick={() => {
                if (navigate) {
                  navigate('docs');
                } else {
                  window.location.hash = 'docs';
                }
                setActiveNavItem('docs');
              }}
            >
              Docs
            </button>
            <button 
              className={`nav-item ${activeNavItem === 'contact' ? 'active' : ''}`}
              onClick={() => {
                scrollToSection('contact');
                setActiveNavItem('contact');
              }}
            >
              Contact Us
            </button>
            <button 
              className="nav-item dashboard-link"
              onClick={() => window.open('http://localhost:3000/dashboard', '_blank')}
            >
              Dashboard
            </button>
          </div>

          <div className="nav-actions">
            <button 
              className="btn btn-login"
              onClick={() => window.open('http://localhost:3000/login', '_blank')}
            >
              Log in
            </button>
          </div>

          <button 
            className={`nav-toggle ${isMenuOpen ? 'active' : ''}`}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="hero" className="hero">
        <div className="hero-background">
          <Hyperspeed effectOptions={hyperspeedOptions} />
        </div>
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              AI Risk Mitigation System
            </h1>
            <p className="hero-subtitle">
              Secure your AI applications with real-time threat detection, bias protection, and comprehensive compliance monitoring.
            </p>
            <div className="hero-buttons">
              <button 
                className="btn btn-primary"
                onClick={() => window.open('http://localhost:3000/login', '_blank')}
              >
                Get started
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => window.open('http://localhost:3000/dashboard', '_blank')}
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
        <div className="hero-scroll-indicator">
          <span>Scroll to explore</span>
          <div className="scroll-arrow"></div>
        </div>
      </section>

      {/* Core Features */}
      <section id="features" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Complete AI Security Platform</h2>
            <p>End-to-end protection with 100% workflow coverage, from input to output</p>
          </div>
          
          <div className="features-showcase">
            {/* Primary Features Grid */}
            <div className="primary-features">
              <div className="feature-card-large">

                <h3>Complete Workflow Implementation</h3>
                <p>Full end-to-end pipeline: Risk Detection → Mitigation → LLM → Data Access → Output Processing</p>
                <div className="feature-stats">
                  <div className="stat">
                    <span className="stat-number">100%</span>
                    <span className="stat-label">Coverage</span>
                  </div>
                  <div className="stat">
                    <span className="stat-number">&lt;50ms</span>
                    <span className="stat-label">Processing</span>
                  </div>
                </div>
              </div>
              
              <div className="feature-card-large">

                <h3>Advanced Token Remapping</h3>
                <p>Secure storage, encryption, audit trails, and automatic expiration for sensitive data</p>
                <div className="feature-stats">
                  <div className="stat">
                    <span className="stat-number">AES-256</span>
                    <span className="stat-label">Encryption</span>
                  </div>
                  <div className="stat">
                    <span className="stat-number">100%</span>
                    <span className="stat-label">Auditable</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Detection Capabilities */}
            <div className="detection-grid">
              <div className="detection-card">

                <h4>PII Detection Engine</h4>
                <p>Microsoft Presidio + spaCy NER + Custom Regex for 25+ data types</p>
                <div className="detection-types">
                  <span>SSNs & Tax IDs</span>
                  <span>Credit Cards</span>
                  <span>API Keys & JWT</span>
                  <span>Medical Records</span>
                  <span>Financial Data</span>
                  <span>Personal Names</span>
                </div>
              </div>
              
              <div className="detection-card">

                <h4>Bias & Fairness Analysis</h4>
                <p>Fairlearn + IBM AIF360 + Custom heuristics for comprehensive bias detection</p>
                <div className="detection-types">
                  <span>Gender Bias</span>
                  <span>Racial Discrimination</span>
                  <span>Age Bias</span>
                  <span>Religious Bias</span>
                  <span>Context-Aware Analysis</span>
                  <span>Fairness Metrics</span>
                </div>
              </div>
              
              <div className="detection-card">

                <h4>Adversarial Protection</h4>
                <p>TextAttack + ART + Custom patterns for advanced threat detection</p>
                <div className="detection-types">
                  <span>Prompt Injection</span>
                  <span>Jailbreak Attempts</span>
                  <span>Role Playing Attacks</span>
                  <span>Social Engineering</span>
                  <span>Gradient-Based Attacks</span>
                  <span>Real-time Blocking</span>
                </div>
              </div>
              
              <div className="detection-card">

                <h4>Hallucination Detection</h4>
                <p>Advanced fact-checking, source validation, and contradiction detection</p>
                <div className="detection-types">
                  <span>Fact Verification</span>
                  <span>Source Validation</span>
                  <span>Contradiction Detection</span>
                  <span>Unverifiable Claims</span>
                  <span>Accuracy Scoring</span>
                  <span>Risk Assessment</span>
                </div>
              </div>

              <div className="detection-card">

                <h4>Query Generation</h4>
                <p>Natural language to SQL with security validation and risk assessment</p>
                <div className="detection-types">
                  <span>NL to SQL</span>
                  <span>Template-Based</span>
                  <span>Security Validation</span>
                  <span>Risk Assessment</span>
                  <span>Query Optimization</span>
                  <span>Pattern Detection</span>
                </div>
              </div>

              <div className="detection-card">

                <h4>Secure Data Access</h4>
                <p>Multi-database connectors with automatic sanitization and PII protection</p>
                <div className="detection-types">
                  <span>PostgreSQL</span>
                  <span>MySQL</span>
                  <span>Supabase</span>
                  <span>REST APIs</span>
                  <span>Auto-Sanitization</span>
                  <span>Zero Raw PII</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>





            {/* Integration & APIs */}
      <section id="integration" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Enterprise API Suite</h2>
            <p>Complete OpenAI-compatible API with advanced risk management endpoints</p>
          </div>
          
          <div className="integration-showcase">
            <div className="api-demo">
              <div className="api-header">
                <h3>Multi-Model Support with Risk Awareness</h3>
                <p>Drop-in replacement for OpenAI, Anthropic, and more with automatic risk detection</p>
              </div>

              {/* Model Support Pills */}
              <div className="model-support">
                <div className="model-pill">🤖 GPT-4</div>
                <div className="model-pill">🧠 Claude</div>
                <div className="model-pill">⚡ Gemini</div>
                <div className="model-pill">🦜 LLaMA</div>
                <div className="model-pill">🔬 Mistral</div>
                <div className="model-pill">+ More</div>
              </div>
              
              <div className="code-flow-comparison">
                <div className="code-section standard">
                  <div className="code-label">
                    <span className="label-icon">⚠️</span>
                    Standard Implementation
                  </div>
                  <div className="code-block">
                    <code>{`// Vulnerable to PII leaks & security risks
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [
    {role: "user", content: "My SSN is 123-45-6789, help me with taxes"}
  ]
});

// No protection against:
// → PII exposure
// → Prompt injection
// → Data leakage
// → Compliance violations`}</code>
                  </div>
                </div>

                <div className="flow-divider">
                  <div className="flow-arrow">→</div>
                  <div className="flow-text">Upgrade to</div>
                </div>
                
                <div className="code-section protected">
                  <div className="code-label">
                    <span className="label-icon">🛡️</span>
                    SecureFlow Protected
                  </div>
                  <div className="code-block">
                    <code>{`// Enterprise-grade security & compliance
const response = await secureflow.chat.completions.create({
  model: "gpt-4", // Works with any model
  messages: [
    {role: "user", content: "My SSN is 123-45-6789, help me with taxes"}
  ],
  risk_aware: true // Enhanced security mode
});

// Automatic protection:
// → PII detection & tokenization
// → Risk metadata in response
// → Compliance audit trails
// → Real-time threat blocking`}</code>
                  </div>
                </div>
              </div>
              
              <div className="api-endpoints">
                <h4>Available API Endpoints</h4>
                <div className="endpoint-list">
                  <div className="endpoint-item">
                    <span className="endpoint-method">POST</span>
                    <span className="endpoint-path">/v1/chat/completions</span>
                    <span className="endpoint-desc">OpenAI-compatible chat with risk detection</span>
                  </div>
                  <div className="endpoint-item">
                    <span className="endpoint-method">POST</span>
                    <span className="endpoint-path">/api/v1/risk/analyze</span>
                    <span className="endpoint-desc">Comprehensive risk analysis for any text</span>
                  </div>
                  <div className="endpoint-item">
                    <span className="endpoint-method">GET</span>
                    <span className="endpoint-path">/api/v1/risk/check</span>
                    <span className="endpoint-desc">Quick safety validation with risk scoring</span>
                  </div>
                  <div className="endpoint-item">
                    <span className="endpoint-method">POST</span>
                    <span className="endpoint-path">/api/v1/query/generate</span>
                    <span className="endpoint-desc">Natural language to SQL with security validation</span>
                  </div>
                  <div className="endpoint-item">
                    <span className="endpoint-method">GET</span>
                    <span className="endpoint-path">/api/v1/analytics/dashboard</span>
                    <span className="endpoint-desc">Real-time risk statistics and monitoring</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="api-features">
              <div className="api-feature" data-parallax="0.1">
                <div className="api-feature-content">
                  <h4>OpenAI Compatible</h4>
                  <p>100% compatible with existing OpenAI API integrations</p>
                  <span className="api-feature-secondary">Drop-in replacement</span>
                </div>
              </div>
              
              <div className="api-feature" data-parallax="0.2">
                <div className="api-feature-content">
                  <h4>Multi-LLM Support</h4>
                  <p>Groq, Anthropic, OpenAI - switch providers seamlessly</p>
                  <span className="api-feature-secondary">5+ providers supported</span>
                </div>
              </div>
              
              <div className="api-feature" data-parallax="0.3">
                <div className="api-feature-content">
                  <h4>Advanced Analytics</h4>
                  <p>Risk timeline, threat detection, and compliance reporting</p>
                  <span className="api-feature-secondary">Real-time insights</span>
                </div>
              </div>
              
              <div className="api-feature" data-parallax="0.1">
                <div className="api-feature-content">
                  <h4>Enterprise Security</h4>
                  <p>API key management, rate limiting, and audit trails</p>
                  <span className="api-feature-secondary">SOC 2 compliant</span>
                </div>
              </div>
              
              <div className="api-feature" data-parallax="0.2">
                <div className="api-feature-content">
                  <h4>Risk Metadata</h4>
                  <p>Detailed risk scores and mitigation actions in every response</p>
                  <span className="api-feature-secondary">100% coverage</span>
                </div>
              </div>
              
              <div className="api-feature" data-parallax="0.3">
                <div className="api-feature-content">
                  <h4>Query Generation</h4>
                  <p>Natural language to SQL with automatic security validation</p>
                  <span className="api-feature-secondary">Zero SQL injection</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials & Social Proof */}
      <section id="testimonials" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Trusted by Industry Leaders</h2>
            <p>Join thousands of developers and enterprises securing their AI applications</p>
          </div>
          
          <div className="testimonials-showcase">
            {/* Stats */}
            <div className="social-stats">
              <div className="stat-card">
                <div className="stat-number">25+</div>
                <div className="stat-label">PII Data Types</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">100%</div>
                <div className="stat-label">Workflow Coverage</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">&lt;50ms</div>
                <div className="stat-label">Processing Time</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">5</div>
                <div className="stat-label">LLM Providers</div>
              </div>
            </div>

            {/* Testimonials Carousel */}
            <div className="testimonials-carousel">
              <div className="carousel-container">
                <button 
                  className="carousel-nav prev" 
                  onClick={prevTestimonial}
                  aria-label="Previous testimonial"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M15 18L9 12L15 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>

                <div className="carousel-content">
                  <div className="testimonial-card active">
                <div className="testimonial-content">
                      <p>"{testimonials[currentTestimonial].quote}"</p>
                </div>
                <div className="testimonial-author">
                      <div className="author-avatar">{testimonials[currentTestimonial].avatar}</div>
                  <div className="author-info">
                        <div className="author-name">{testimonials[currentTestimonial].name}</div>
                        <div className="author-role">{testimonials[currentTestimonial].role}</div>
                      </div>
                  </div>
                </div>
              </div>

                <button 
                  className="carousel-nav next" 
                  onClick={nextTestimonial}
                  aria-label="Next testimonial"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>

              {/* Carousel Dots */}
              <div className="carousel-dots">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    className={`carousel-dot ${index === currentTestimonial ? 'active' : ''}`}
                    onClick={() => goToTestimonial(index)}
                    aria-label={`Go to testimonial ${index + 1}`}
                  />
                ))}
              </div>
            </div>


          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing">
        <Pricing />
      </section>



      {/* Contact */}
      <section id="contact" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Contact Us</h2>
            <p>Get in touch with our team for support, questions, or to get started</p>
          </div>
          
          <div className="contact-content">
            <div className="contact-info">
              <div className="contact-item">
                <h3>📧 Email Support</h3>
                <p>support@airms.com</p>
                <span>24/7 technical support</span>
              </div>
              

              
              <div className="contact-item">
                <h3>📞 Sales Inquiries</h3>
                <p>sales@airms.com</p>
                <span>Enterprise solutions & pricing</span>
              </div>
            </div>
            
            <div className="contact-form">
              <h3>Send us a message</h3>
              <form>
                <div className="form-group">
                  <input type="text" placeholder="Your Name" required />
                </div>
                <div className="form-group">
                  <input type="email" placeholder="Your Email" required />
                </div>
                <div className="form-group">
                  <textarea placeholder="Your Message" rows={4} required></textarea>
                </div>
                <button type="submit" className="btn btn-primary">
                  Send Message
                </button>
              </form>
            </div>
          </div>
          
          <div className="cta-section">
            <h3>Ready to get started?</h3>
            <p>Protect your AI data in minutes, not months.</p>
            <div className="cta-buttons">
              <button 
                className="btn btn-primary"
                onClick={() => window.open('http://localhost:3000/login', '_blank')}
              >
                Start free trial
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => window.open('http://localhost:3000/dashboard', '_blank')}
              >
                Access Dashboard
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="modern-footer">
        {/* Floating Particles */}
        <div className="footer-particles">
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
        </div>
        
        <div className="footer-container">
          {/* Main Footer Content */}
          <div className="footer-main">
            {/* Brand Section */}
            <div className="footer-brand">
              <div className="footer-logo">
                <span className="logo-text">AIRMS</span>
                <span className="logo-tagline">AI Risk Management System</span>
              </div>
              <p className="footer-description">
                Protect your AI applications with real-time threat detection, bias analysis, 
                and comprehensive compliance monitoring.
              </p>
            </div>
            
            {/* Social Links */}
            <div className="social-links">
              <a href="#twitter" className="social-link" aria-label="Twitter">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                </svg>
              </a>
              <a href="#linkedin" className="social-link" aria-label="LinkedIn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </a>
              <a href="#github" className="social-link" aria-label="GitHub">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              <a href="#discord" className="social-link" aria-label="Discord">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419-.0190 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1568 2.4189Z"/>
                </svg>
              </a>
            </div>

            {/* Essential Links */}
            <div className="footer-section">
              <h4>Essential</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#docs">Documentation</a></li>
                <li><a href="#contact">Contact Us</a></li>
                <li><a href="http://localhost:3000/dashboard" target="_blank" rel="noopener noreferrer">Dashboard</a></li>
              </ul>
            </div>


          </div>

          {/* Footer Bottom */}
          <div className="footer-bottom">
            <div className="footer-bottom-content">
              <div className="footer-legal">
                <span>© 2024 AIRMS. All rights reserved.</span>
                <div className="legal-links">
                  <a href="#privacy">Privacy Policy</a>
                  <a href="#terms">Terms of Service</a>
                </div>
              </div>
              <div className="footer-status">
                <span className="status-indicator">
                  <span className="status-dot"></span>
                  All systems operational
                </span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

