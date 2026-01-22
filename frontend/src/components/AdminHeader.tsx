import { useNavigate, useLocation } from 'react-router-dom';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
} from '@carbon/react';
import {
  Add,
  Renew,
  Logout,
  CheckmarkOutline,
} from '@carbon/icons-react';
import NotificationBell from './NotificationBell';
import { useAuth } from '../context/AuthContext';

interface AdminHeaderProps {
  title?: string;
  subtitle?: string;
  onGenerateBrief?: () => void;
  generating?: boolean;
  showBackButton?: boolean;
  onBack?: () => void;
  onRefresh?: () => void;
  refreshing?: boolean;
}

export default function AdminHeader({
  title = 'Signal Management',
  subtitle,
  onGenerateBrief,
  generating = false,
  onRefresh,
  refreshing = false
}: AdminHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

  return (
    <HeaderContainer
      render={() => (
        <>
          <Header aria-label="MarketPulse">
            <SkipToContent />
            <HeaderName href="#" prefix="" onClick={(e) => {
              e.preventDefault();
              navigate('/');
            }}>
              MarketPulse
            </HeaderName>
            <HeaderNavigation aria-label="MarketPulse">
              <HeaderMenuItem onClick={() => navigate('/')} isCurrentPage={location.pathname === '/'}>
                Dashboard
              </HeaderMenuItem>
              <HeaderMenuItem onClick={() => navigate('/admin/signals')} isCurrentPage={location.pathname === '/admin/signals'}>
                Signals
              </HeaderMenuItem>
              <HeaderMenuItem onClick={() => navigate('/admin/signals/review')} isCurrentPage={location.pathname === '/admin/signals/review'}>
                Review Pending
              </HeaderMenuItem>
              <HeaderMenuItem onClick={() => navigate('/admin/data-sources')} isCurrentPage={location.pathname === '/admin/data-sources'}>
                Data Sources
              </HeaderMenuItem>
              <HeaderMenuItem onClick={() => navigate('/admin/entities')} isCurrentPage={location.pathname === '/admin/entities'}>
                Entities
              </HeaderMenuItem>
              <HeaderMenuItem onClick={() => navigate('/admin/evaluations')} isCurrentPage={location.pathname === '/admin/evaluations'}>
                Evaluations
              </HeaderMenuItem>
            </HeaderNavigation>
            <HeaderGlobalBar>
              {onRefresh && (
                <HeaderGlobalAction
                  aria-label="Refresh"
                  tooltipAlignment="end"
                  onClick={onRefresh}
                  isActive={refreshing}
                >
                  <Renew size={20} />
                </HeaderGlobalAction>
              )}
              {onGenerateBrief && (
                <HeaderGlobalAction
                  aria-label="Generate Weekly Brief"
                  tooltipAlignment="end"
                  onClick={onGenerateBrief}
                  isActive={generating}
                >
                  <CheckmarkOutline size={20} />
                </HeaderGlobalAction>
              )}
              <HeaderGlobalAction
                aria-label="Add Signal"
                tooltipAlignment="end"
                onClick={() => navigate('/admin/signals/new')}
              >
                <Add size={20} />
              </HeaderGlobalAction>
              <div style={{ display: 'flex', alignItems: 'center', paddingRight: '1rem' }}>
                <NotificationBell />
              </div>
              <HeaderGlobalAction
                aria-label="Logout"
                tooltipAlignment="end"
                onClick={logout}
              >
                <Logout size={20} />
              </HeaderGlobalAction>
            </HeaderGlobalBar>
          </Header>
          {(title || subtitle) && (
            <div className="cds--content" style={{
              background: 'var(--cds-background)',
              borderBottom: '1px solid var(--cds-border-subtle)',
              padding: '1rem'
            }}>
              <h1 style={{
                fontSize: '1.75rem',
                fontWeight: 600,
                marginBottom: '0.25rem',
                color: 'var(--cds-text-primary)'
              }}>
                {title}
              </h1>
              {subtitle && (
                <p style={{
                  fontSize: '0.875rem',
                  color: 'var(--cds-text-secondary)'
                }}>
                  {subtitle}
                </p>
              )}
            </div>
          )}
        </>
      )}
    />
  );
}
