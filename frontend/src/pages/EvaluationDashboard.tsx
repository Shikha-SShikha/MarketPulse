import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tile,
  Grid,
  Column,
  Loading,
  Tag,
  Dropdown,
  ProgressBar,
  Button,
} from '@carbon/react';
import { CheckmarkFilled, WarningFilled, ErrorFilled, Play } from '@carbon/icons-react';
import { apiClient } from '../api/client';
import AdminHeader from '../components/AdminHeader';

interface EvaluationIssue {
  id: string;
  issue_type: string;
  severity: string;
  description: string;
  affected_signal_ids: string[] | null;
  affected_entities: string[] | null;
  created_at: string;
}

interface EvaluationRun {
  id: string;
  content_type: string;
  content_id: string;
  hallucination_score: number;
  grounding_score: number;
  relevance_score: number;
  actionability_score: number;
  coherence_score: number;
  overall_score: number;
  passed: boolean;
  threshold: number;
  evaluator_model: string;
  evaluation_method: string;
  created_at: string;
  issues: EvaluationIssue[];
}

interface EvaluationStats {
  total_evaluations: number;
  passed_count: number;
  failed_count: number;
  pass_rate: number;
  avg_hallucination_score: number;
  avg_grounding_score: number;
  avg_relevance_score: number;
  avg_actionability_score: number;
  avg_coherence_score: number;
  avg_overall_score: number;
  issue_counts: Record<string, number>;
  recent_failures: EvaluationRun[];
}

export default function EvaluationDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<EvaluationStats | null>(null);
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [daysFilter, setDaysFilter] = useState(30);
  const [passedFilter, setPassedFilter] = useState<'all' | 'passed' | 'failed'>('all');

  useEffect(() => {
    loadData();
  }, [daysFilter, passedFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load stats
      const statsResponse = await apiClient.get<EvaluationStats>(
        `/evaluations/stats?days=${daysFilter}`
      );
      setStats(statsResponse.data);

      // Load evaluations
      const evalsResponse = await apiClient.get<EvaluationRun[]>('/evaluations', {
        params: {
          passed: passedFilter === 'all' ? undefined : passedFilter === 'passed',
          limit: 50,
        },
      });
      setEvaluations(evalsResponse.data);
    } catch (error) {
      console.error('Failed to load evaluation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluations = async () => {
    setEvaluating(true);
    try {
      // Trigger evaluation of current brief
      const response = await apiClient.post('/admin/evaluate-brief', null, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('curator_token')}`,
        },
      });

      alert(`Evaluation complete!\nBrief evaluated: ${response.data.evaluated_count} themes\nPassed: ${response.data.passed_count}/${response.data.evaluated_count}`);

      // Reload data
      await loadData();
    } catch (error) {
      console.error('Failed to run evaluations:', error);
      alert('Failed to run evaluations. Check console for details.');
    } finally {
      setEvaluating(false);
    }
  };

  const getScoreColor = (score: number, threshold: number = 9.5): string => {
    if (score >= threshold) return 'green';
    if (score >= threshold - 1) return 'yellow';
    return 'red';
  };

  const getSeverityTag = (severity: string): 'red' | 'warm-gray' | 'blue' | 'gray' => {
    const severityMap: Record<string, 'red' | 'warm-gray' | 'blue' | 'gray'> = {
      critical: 'red',
      major: 'warm-gray',
      minor: 'blue',
    };
    return (severityMap[severity.toLowerCase()] as 'red' | 'warm-gray' | 'blue' | 'gray') || 'gray';
  };

  if (loading && !stats) {
    return (
      <div style={{ padding: '2rem', display: 'flex', justifyContent: 'center' }}>
        <Loading description="Loading evaluation data..." />
      </div>
    );
  }

  if (!stats) {
    return (
      <div style={{ padding: '2rem' }}>
        <p>No evaluation data available.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <AdminHeader
        title="Evaluation Monitoring Dashboard"
        subtitle="Track AI output quality metrics and identify issues"
        showBackButton={true}
        onBack={() => navigate('/admin/signals')}
      />

      <main className="cds--content" style={{ padding: '2rem' }}>
        <div className="max-w-7xl mx-auto">
          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
            <Button
              renderIcon={Play}
              onClick={handleRunEvaluations}
              disabled={evaluating}
              kind="primary"
            >
              {evaluating ? 'Evaluating...' : 'Run Evaluation on Current Brief'}
            </Button>

            <Dropdown
              id="days-filter"
              titleText="Time Range"
              label="Select time range"
              items={[
                { id: '7', label: 'Last 7 days' },
                { id: '30', label: 'Last 30 days' },
                { id: '90', label: 'Last 90 days' },
              ]}
              selectedItem={{ id: String(daysFilter), label: `Last ${daysFilter} days` }}
              onChange={({ selectedItem }) => {
                if (selectedItem) setDaysFilter(Number(selectedItem.id));
              }}
            />

            <Dropdown
              id="passed-filter"
              titleText="Status Filter"
              label="Select status"
              items={[
                { id: 'all', label: 'All evaluations' },
                { id: 'passed', label: 'Passed only' },
                { id: 'failed', label: 'Failed only' },
              ]}
              selectedItem={{ id: passedFilter, label: passedFilter === 'all' ? 'All evaluations' : passedFilter === 'passed' ? 'Passed only' : 'Failed only' }}
              onChange={({ selectedItem }) => {
                if (selectedItem) setPassedFilter(selectedItem.id as 'all' | 'passed' | 'failed');
              }}
            />
          </div>

      {/* Summary Stats */}
      <Grid style={{ marginBottom: '2rem' }}>
        <Column lg={4} md={4} sm={4}>
          <Tile style={{ height: '100%', padding: '1.5rem' }}>
            <div style={{ marginBottom: '0.5rem', color: '#525252', fontSize: '0.875rem' }}>
              Total Evaluations
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              {stats.total_evaluations}
            </div>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
              <span style={{ color: '#24a148' }}>
                <CheckmarkFilled size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                {stats.passed_count} passed
              </span>
              <span style={{ color: '#da1e28' }}>
                <ErrorFilled size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                {stats.failed_count} failed
              </span>
            </div>
          </Tile>
        </Column>

        <Column lg={4} md={4} sm={4}>
          <Tile style={{ height: '100%', padding: '1.5rem' }}>
            <div style={{ marginBottom: '0.5rem', color: '#525252', fontSize: '0.875rem' }}>
              Pass Rate
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              {stats.pass_rate.toFixed(1)}%
            </div>
            <ProgressBar
              label=""
              value={stats.pass_rate}
              max={100}
              status={stats.pass_rate >= 95 ? 'finished' : stats.pass_rate >= 80 ? 'active' : 'error'}
            />
            <div style={{ fontSize: '0.75rem', color: '#525252', marginTop: '0.5rem' }}>
              Target: 95%
            </div>
          </Tile>
        </Column>

        <Column lg={4} md={4} sm={4}>
          <Tile style={{ height: '100%', padding: '1.5rem' }}>
            <div style={{ marginBottom: '0.5rem', color: '#525252', fontSize: '0.875rem' }}>
              Average Overall Score
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              {stats.avg_overall_score.toFixed(2)}
              <span style={{ fontSize: '1rem', color: '#525252' }}>/10</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#525252' }}>
              {stats.avg_overall_score >= 9.5 ? '✅ Exceeds target' : stats.avg_overall_score >= 9.0 ? '⚠️ Approaching target' : '❌ Below target'}
            </div>
          </Tile>
        </Column>
      </Grid>

      {/* Score Breakdown */}
      <Tile style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
          Score Breakdown
        </h3>
        <Grid>
          <Column lg={3} md={4} sm={4}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Hallucination</span>
                <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                  {stats.avg_hallucination_score.toFixed(2)}
                </span>
              </div>
              <ProgressBar
                label=""
                value={stats.avg_hallucination_score * 10}
                max={100}
                status={getScoreColor(stats.avg_hallucination_score) === 'green' ? 'finished' : 'active'}
              />
            </div>
          </Column>

          <Column lg={3} md={4} sm={4}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Grounding</span>
                <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                  {stats.avg_grounding_score.toFixed(2)}
                </span>
              </div>
              <ProgressBar
                label=""
                value={stats.avg_grounding_score * 10}
                max={100}
                status={getScoreColor(stats.avg_grounding_score) === 'green' ? 'finished' : 'active'}
              />
            </div>
          </Column>

          <Column lg={3} md={4} sm={4}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Relevance</span>
                <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                  {stats.avg_relevance_score.toFixed(2)}
                </span>
              </div>
              <ProgressBar
                label=""
                value={stats.avg_relevance_score * 10}
                max={100}
                status={getScoreColor(stats.avg_relevance_score) === 'green' ? 'finished' : 'active'}
              />
            </div>
          </Column>

          <Column lg={3} md={4} sm={4}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Actionability</span>
                <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                  {stats.avg_actionability_score.toFixed(2)}
                </span>
              </div>
              <ProgressBar
                label=""
                value={stats.avg_actionability_score * 10}
                max={100}
                status={getScoreColor(stats.avg_actionability_score) === 'green' ? 'finished' : 'active'}
              />
            </div>
          </Column>

          <Column lg={3} md={4} sm={4}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.875rem' }}>Coherence</span>
                <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                  {stats.avg_coherence_score.toFixed(2)}
                </span>
              </div>
              <ProgressBar
                label=""
                value={stats.avg_coherence_score * 10}
                max={100}
                status={getScoreColor(stats.avg_coherence_score) === 'green' ? 'finished' : 'active'}
              />
            </div>
          </Column>
        </Grid>
      </Tile>

      {/* Issue Breakdown */}
      {Object.keys(stats.issue_counts).length > 0 && (
        <Tile style={{ marginBottom: '2rem', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            Issues Found
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {Object.entries(stats.issue_counts).map(([type, count]) => (
              <div
                key={type}
                style={{
                  padding: '1rem',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  minWidth: '150px',
                }}
              >
                <div style={{ fontSize: '0.875rem', color: '#525252', marginBottom: '0.25rem' }}>
                  {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{count}</div>
              </div>
            ))}
          </div>
        </Tile>
      )}

      {/* Recent Evaluations */}
      <Tile style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
          Recent Evaluations
        </h3>

        <DataTable
          rows={evaluations.map((evaluation) => ({
            id: evaluation.id,
            content_type: evaluation.content_type,
            overall_score: evaluation.overall_score,
            passed: evaluation.passed,
            hallucination: evaluation.hallucination_score,
            grounding: evaluation.grounding_score,
            relevance: evaluation.relevance_score,
            actionability: evaluation.actionability_score,
            coherence: evaluation.coherence_score,
            issues: evaluation.issues.length,
            created_at: new Date(evaluation.created_at).toLocaleString(),
          }))}
          headers={[
            { key: 'content_type', header: 'Content Type' },
            { key: 'overall_score', header: 'Overall Score' },
            { key: 'passed', header: 'Status' },
            { key: 'hallucination', header: 'Hallucination' },
            { key: 'grounding', header: 'Grounding' },
            { key: 'relevance', header: 'Relevance' },
            { key: 'actionability', header: 'Actionability' },
            { key: 'coherence', header: 'Coherence' },
            { key: 'issues', header: 'Issues' },
            { key: 'created_at', header: 'Created' },
          ]}
        >
          {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
            <TableContainer>
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((header) => (
                      <TableHeader {...getHeaderProps({ header })} key={header.key}>
                        {header.header}
                      </TableHeader>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => {
                    const evalData = evaluations.find((e) => e.id === row.id);
                    return (
                      <TableRow {...getRowProps({ row })} key={row.id}>
                        {row.cells.map((cell) => {
                          if (cell.info.header === 'content_type') {
                            return (
                              <TableCell key={cell.id}>
                                <Tag type="blue">{cell.value}</Tag>
                              </TableCell>
                            );
                          }
                          if (cell.info.header === 'overall_score') {
                            return (
                              <TableCell key={cell.id}>
                                <strong style={{ color: evalData && evalData.overall_score >= 9.5 ? '#24a148' : evalData && evalData.overall_score >= 9.0 ? '#f1c21b' : '#da1e28' }}>
                                  {Number(cell.value).toFixed(2)}
                                </strong>
                                /10
                              </TableCell>
                            );
                          }
                          if (cell.info.header === 'passed') {
                            return (
                              <TableCell key={cell.id}>
                                {cell.value ? (
                                  <Tag type="green" renderIcon={CheckmarkFilled}>
                                    Passed
                                  </Tag>
                                ) : (
                                  <Tag type="red" renderIcon={ErrorFilled}>
                                    Failed
                                  </Tag>
                                )}
                              </TableCell>
                            );
                          }
                          if (
                            ['hallucination', 'grounding', 'relevance', 'actionability', 'coherence'].includes(
                              cell.info.header
                            )
                          ) {
                            return (
                              <TableCell key={cell.id}>
                                <span style={{ fontSize: '0.875rem' }}>
                                  {Number(cell.value).toFixed(1)}
                                </span>
                              </TableCell>
                            );
                          }
                          if (cell.info.header === 'issues') {
                            return (
                              <TableCell key={cell.id}>
                                {cell.value > 0 ? (
                                  <Tag type="gray" renderIcon={WarningFilled}>
                                    {cell.value}
                                  </Tag>
                                ) : (
                                  <span style={{ color: '#525252' }}>-</span>
                                )}
                              </TableCell>
                            );
                          }
                          return <TableCell key={cell.id}>{cell.value}</TableCell>;
                        })}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DataTable>

        {evaluations.length === 0 && (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#525252' }}>
            No evaluations found for the selected filters.
          </div>
        )}
      </Tile>

      {/* Recent Failures Detail */}
      {stats.recent_failures.length > 0 && (
        <Tile style={{ marginTop: '2rem', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#da1e28' }}>
            <ErrorFilled size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Recent Failures Requiring Attention
          </h3>

          {stats.recent_failures.map((failure) => (
            <div
              key={failure.id}
              style={{
                padding: '1rem',
                marginBottom: '1rem',
                border: '1px solid #da1e28',
                borderLeft: '4px solid #da1e28',
                borderRadius: '4px',
                backgroundColor: '#fff1f1',
              }}
            >
              <div style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <Tag type="blue">{failure.content_type}</Tag>
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.875rem', color: '#525252' }}>
                    {new Date(failure.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ fontSize: '1rem', fontWeight: '600', color: '#da1e28' }}>
                  Score: {failure.overall_score.toFixed(2)}/10
                </div>
              </div>

              <div style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                <strong>Score Breakdown:</strong> Hallucination: {failure.hallucination_score.toFixed(1)} |
                Grounding: {failure.grounding_score.toFixed(1)} |
                Relevance: {failure.relevance_score.toFixed(1)} |
                Actionability: {failure.actionability_score.toFixed(1)} |
                Coherence: {failure.coherence_score.toFixed(1)}
              </div>

              {failure.issues.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <strong style={{ fontSize: '0.875rem' }}>Issues Found:</strong>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                    {failure.issues.map((issue) => (
                      <li key={issue.id} style={{ marginBottom: '0.5rem' }}>
                        <Tag type={getSeverityTag(issue.severity)} size="sm">
                          {issue.severity}
                        </Tag>{' '}
                        <strong>{issue.issue_type}:</strong> {issue.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </Tile>
      )}
        </div>
      </main>
    </div>
  );
}
