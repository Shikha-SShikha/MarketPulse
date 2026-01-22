import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSegmentStats } from '../api/segments';
import type { SegmentStats } from '../types';

const SEGMENT_CONFIG = {
  customer: {
    label: 'Customers',
    icon: '👥',
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    hoverBg: 'hover:bg-blue-100',
  },
  competitor: {
    label: 'Competitors',
    icon: '⚔️',
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    hoverBg: 'hover:bg-red-100',
  },
  industry: {
    label: 'Industry',
    icon: '🏛️',
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    hoverBg: 'hover:bg-green-100',
  },
  influencer: {
    label: 'Influencers',
    icon: '⭐',
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
    hoverBg: 'hover:bg-purple-100',
  },
};

export default function SegmentStatsWidget() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SegmentStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getSegmentStats(7);
      setStats(response.stats);
    } catch (err: any) {
      console.error('Failed to load segment stats:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load segment statistics';
      setError(`Failed to load segment statistics: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (segment: string) => {
    navigate(`/signals?segment=${segment}`);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-gray-100 rounded-lg p-6 animate-pulse"
            style={{ height: '140px' }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Segment Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const config = SEGMENT_CONFIG[stat.segment as keyof typeof SEGMENT_CONFIG];

          if (!config) return null;

          return (
            <div
              key={stat.segment}
              onClick={() => handleCardClick(stat.segment)}
              className={`${config.bgColor} ${config.borderColor} ${config.hoverBg} border-2 rounded-lg p-6 cursor-pointer transition-all hover:shadow-md`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">{config.icon}</span>
                <span className={`${config.textColor} text-xs font-medium px-2 py-1 rounded-full bg-white`}>
                  {stat.entity_count} {stat.entity_count === 1 ? 'entity' : 'entities'}
                </span>
              </div>

              <h3 className={`${config.textColor} font-semibold text-lg mb-2`}>
                {config.label}
              </h3>

              <div className="space-y-1">
                <div className="flex items-baseline justify-between">
                  <span className="text-gray-600 text-sm">Recent (7d):</span>
                  <span className={`${config.textColor} font-bold text-2xl`}>
                    {stat.recent_signals}
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-gray-500 text-xs">Total signals:</span>
                  <span className="text-gray-700 text-sm font-medium">
                    {stat.signal_count}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
