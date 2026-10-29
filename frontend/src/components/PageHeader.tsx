import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, ArrowRight } from 'lucide-react';
import './PageHeader.css';

interface CrossLink {
  label: string;
  path: string;
  icon?: any;
}

interface PageHeaderProps {
  hub: string;
  title: string;
  subtitle: string;
  badge?: string;
  badgeType?: 'live' | 'ai' | 'prob' | 'cyan' | 'green' | 'gold';
  crossLinks?: CrossLink[];
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  hub,
  title,
  subtitle,
  badge,
  badgeType = 'cyan',
  crossLinks = []
}) => {
  return (
    <div className="page-header-container">
      <div className="page-header-left">
        {/* Breadcrumb Hierarchy */}
        <div className="page-breadcrumb">
          <span className="crumb-hub">{hub}</span>
          <ChevronRight size={12} className="crumb-sep" />
          <span className="crumb-current">{title}</span>
        </div>

        {/* Title and Purpose Line */}
        <div className="page-title-row">
          <h1 className="page-main-title">{title}</h1>
          {badge && <span className={`page-title-badge ${badgeType}`}>{badge}</span>}
        </div>
        <p className="page-subtitle">{subtitle}</p>
      </div>

      {/* Contextual Cross-Links */}
      {crossLinks.length > 0 && (
        <div className="page-header-actions">
          <span className="actions-label">RELATED WORKFLOWS:</span>
          <div className="cross-links-group">
            {crossLinks.map((link, idx) => {
              const Icon = link.icon || ArrowRight;
              return (
                <Link key={idx} to={link.path} className="cross-link-btn">
                  <Icon size={12} className="link-icon" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
