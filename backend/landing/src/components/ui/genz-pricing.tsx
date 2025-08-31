import React from "react";
import { User, Check, Zap, Building2 } from "lucide-react";

type CTA = {
  label: string;
  href: string;
  variant?: "default" | "glow" | "glow-brand";
};

type Plan = {
  name: string;
  icon?: React.ReactNode;
  description: string;
  price: number;
  priceNote?: string;
  cta: CTA;
  features: string[];
  variant?: "default" | "glow" | "glow-brand";
  className?: string;
};

type PricingProps = {
  title?: string | false;
  description?: string | false;
  className?: string;
};

export default function Pricing({
  title = "Choose Your AIRMS Plan",
  description = "Enterprise AI risk management solutions that scale with your needs. Start free, upgrade as you grow.",
  className = "",
}: PricingProps) {
  // SecureFlow API limits and features
  const stats = {
    freeRequests: "10K",
    starterRequests: "100K", 
    proRequests: "1M",
    enterpriseRequests: "Unlimited",
    detectionTypes: 20,
    supportedModels: 15,
  };

  const plans: Plan[] = [
    {
      name: "Developer",
      icon: <User className="w-4 h-4" />,
      description: "Perfect for individual developers and small projects",
      price: 0,
      priceNote: "Free forever. No credit card required.",
      cta: {
        variant: "glow",
        label: "Start Building",
        href: "/signup",
      },
      features: [
        `${stats.freeRequests} API requests/month`,
        "PII Detection & Redaction",
        "Basic Bias Detection",
        "OpenAI Compatible API",
        "Community Support",
        "Standard Rate Limiting",
      ],
      variant: "default",
    },
    {
      name: "Starter",
      icon: <Zap className="w-4 h-4" />,
      description: "For growing startups and production applications",
      price: 49,
      priceNote: "Per month. Cancel anytime.",
      cta: {
        variant: "glow-brand",
        label: "Start Free Trial",
        href: "/signup?plan=starter",
      },
      features: [
        `${stats.starterRequests} API requests/month`,
        "Advanced PII Detection (${stats.detectionTypes}+ types)",
        "Adversarial Attack Detection",
        "Hallucination Detection",
        "Multi-LLM Support (${stats.supportedModels} providers)",
        "Real-time Analytics Dashboard",
        "Email Support",
        "99.9% SLA",
      ],
      variant: "glow-brand",
    },
    {
      name: "Enterprise",
      icon: <Building2 className="w-4 h-4" />,
      description: "For large organizations with advanced security needs",
      price: 499,
      priceNote: "Per month. Custom volume pricing available.",
      cta: {
        variant: "default",
        label: "Contact Sales",
        href: "/contact-sales",
      },
      features: [
        `${stats.enterpriseRequests} API requests`,
        "Custom Risk Detection Models",
        "Advanced Token Remapping",
        "SOC2 Type II Compliance",
        "GDPR & HIPAA Ready",
        "Dedicated Support Engineer",
        "Custom Integrations",
        "99.99% SLA",
        "On-premises Deployment",
        "Advanced Analytics & Reporting",
      ],
      variant: "glow",
    },
  ];

  return (
    <section
      style={{
        width: '100%',
        padding: '3rem 0 5rem',
        backgroundColor: '#000000',
        minHeight: '100vh',
      }}
      className={className}
    >
      <div style={{ maxWidth: '72rem', margin: '0 auto', padding: '0 1rem' }}>
        {(title || description) && (
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            gap: '1.5rem', 
            textAlign: 'center', 
            marginBottom: '3.5rem' 
          }}>
            {title && (
              <h2 style={{
                fontSize: 'clamp(2rem, 5vw, 3rem)',
                fontWeight: '600',
                lineHeight: '1.2',
                color: 'white',
                letterSpacing: '-0.02em',
                margin: 0,
              }}>
                {title}
              </h2>
            )}
            {description && (
              <p style={{
                fontSize: 'clamp(1rem, 2.5vw, 1.25rem)',
                color: '#d4d4d8',
                maxWidth: '45rem',
                fontWeight: '500',
                margin: 0,
              }}>
                {description}
              </p>
            )}
          </div>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '2rem',
          alignItems: 'stretch',
        }}>
          {plans.map((plan) => (
            <div
              key={plan.name}
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minHeight: '500px',
                borderRadius: '1rem',
                background: plan.variant === 'glow-brand' 
                  ? 'linear-gradient(135deg, rgba(227, 148, 243, 0.1), rgba(108, 68, 161, 0.1))'
                  : 'rgba(253, 253, 253, 0.03)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: plan.variant === 'glow-brand' 
                  ? '1px solid rgba(227, 148, 243, 0.3)'
                  : '1px solid rgba(158, 158, 158, 0.15)',
                boxShadow: plan.variant === 'glow-brand'
                  ? '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 0 50px rgba(227, 148, 243, 0.4)'
                  : '0 20px 25px -5px rgba(0, 0, 0, 0.4)',
                padding: '2rem',
                color: 'white',
                overflow: 'hidden',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.05)';
                e.currentTarget.style.boxShadow = plan.variant === 'glow-brand'
                  ? '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 80px rgba(227, 148, 243, 0.6)'
                  : '0 25px 50px -12px rgba(0, 0, 0, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.boxShadow = plan.variant === 'glow-brand'
                  ? '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 0 50px rgba(227, 148, 243, 0.4)'
                  : '0 20px 25px -5px rgba(0, 0, 0, 0.4)';
              }}
            >
              {/* Glow effect for featured plan */}
              {plan.variant === 'glow-brand' && (
                <div style={{
                  position: 'absolute',
                  top: '-2rem',
                  right: '-2rem',
                  width: '8rem',
                  height: '8rem',
                  borderRadius: '50%',
                  background: 'radial-gradient(circle, rgba(227, 148, 243, 0.4) 0%, transparent 70%)',
                  filter: 'blur(20px)',
                  pointerEvents: 'none',
                }} />
              )}

              {/* Header */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  {plan.icon && (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '1.5rem',
                      height: '1.5rem',
                      borderRadius: '50%',
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                    }}>
                      {plan.icon}
                    </span>
                  )}
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'rgba(255, 255, 255, 0.9)' }}>
                    {plan.name}
                  </span>
                </div>

                <p style={{
                  fontSize: '0.9375rem',
                  color: '#d4d4d8',
                  lineHeight: '1.6',
                  marginBottom: '2rem',
                }}>
                  {plan.description}
                </p>

                {/* Price */}
                <div style={{ marginBottom: '2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'end', gap: '0.75rem', marginBottom: '1.5rem' }}>
                    <span style={{ color: '#d4d4d8', fontSize: '1.25rem', marginBottom: '0.25rem' }}>$</span>
                    <span style={{
                      fontSize: 'clamp(3rem, 8vw, 3.75rem)',
                      fontWeight: '800',
                      letterSpacing: '-0.025em',
                      lineHeight: '1',
                    }}>
                      {plan.price}
                    </span>
                    {plan.name !== "Developer" && (
                      <div style={{ marginBottom: '0.25rem' }}>
                        <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#e5e5e5' }}>
                          {plan.name === "Enterprise" ? "per month" : "per month"}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#a3a3a3' }}>
                          {plan.name === "Enterprise" ? "custom pricing available" : "14-day free trial"}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* CTA Button */}
                  <a
                    href={plan.cta.href}
                    style={{
                      display: 'inline-flex',
                      width: '100%',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '0.5rem',
                      padding: '0.75rem 1rem',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      textDecoration: 'none',
                      transition: 'all 0.2s ease',
                      background: plan.variant === 'glow-brand'
                        ? 'linear-gradient(135deg, #e394f3, #6c44a1)'
                        : 'linear-gradient(135deg, rgba(253, 253, 253, 0.1), rgba(158, 158, 158, 0.1))',
                      color: 'white',
                      border: plan.variant === 'glow-brand'
                        ? '1px solid rgba(227, 148, 243, 0.5)'
                        : '1px solid rgba(158, 158, 158, 0.3)',
                      boxShadow: plan.variant === 'glow-brand'
                        ? '0 4px 14px 0 rgba(227, 148, 243, 0.3)'
                        : '0 4px 14px 0 rgba(0, 0, 0, 0.3)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.05)';
                      e.currentTarget.style.boxShadow = plan.variant === 'glow-brand'
                        ? '0 6px 20px 0 rgba(227, 148, 243, 0.4)'
                        : '0 6px 20px 0 rgba(0, 0, 0, 0.4)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.boxShadow = plan.variant === 'glow-brand'
                        ? '0 4px 14px 0 rgba(227, 148, 243, 0.3)'
                        : '0 4px 14px 0 rgba(0, 0, 0, 0.3)';
                    }}
                  >
                    {plan.cta.label}
                  </a>

                  {/* Price note */}
                  {plan.priceNote && (
                    <p style={{
                      marginTop: '1rem',
                      fontSize: '0.875rem',
                      color: '#a3a3a3',
                    }}>
                      {plan.priceNote}
                    </p>
                  )}
                </div>

                {/* Divider */}
                <div style={{
                  height: '1px',
                  width: '100%',
                  background: 'rgba(255, 255, 255, 0.1)',
                  marginBottom: '1.5rem',
                }} />

                {/* Features */}
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {plan.features.map((feature, index) => (
                    <li key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <span style={{
                        marginTop: '0.125rem',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '1.25rem',
                        height: '1.25rem',
                        borderRadius: '50%',
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        flexShrink: 0,
                      }}>
                        <Check className="w-3.5 h-3.5" style={{ color: 'rgba(255, 255, 255, 0.9)' }} />
                      </span>
                      <span style={{
                        fontSize: '0.9375rem',
                        color: '#e5e5e5',
                        lineHeight: '1.4',
                      }}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}