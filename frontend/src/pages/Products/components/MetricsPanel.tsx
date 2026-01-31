import React from 'react';
import { StatisticCard } from '@ant-design/pro-components';
import { Alert, Row, Col } from 'antd';
import type { ProductMetrics } from '@/services/products';

interface MetricsPanelProps {
  metrics: ProductMetrics | null;
  metricsStatus: 'ok' | 'insufficient_data' | 'degraded';
  metricsDegradedReason?: string;
  hasEvents: boolean;
}

const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  metricsStatus,
  metricsDegradedReason,
  hasEvents,
}) => {
  return (
    <>
      <Row gutter={16}>
        <Col span={12}>
          <StatisticCard
            statistic={{
              title: metricsStatus === 'degraded' ? '估算参考收益率' : '参考收益率',
              value: metrics?.annualized,
              suffix: metrics?.annualized !== undefined ? '%' : '--',
              precision: 2,
            }}
            style={{ marginBottom: 16 }}
          />
        </Col>
        <Col span={12}>
          <StatisticCard
            statistic={{
              title: '时间加权收益',
              value: metrics?.twr,
              suffix: metrics?.twr !== undefined ? '%' : '--',
              precision: 2,
            }}
            style={{ marginBottom: 16 }}
          />
        </Col>
        <Col span={12}>
          <StatisticCard
            statistic={{
              title: '最大回撤',
              value: metrics?.max_drawdown,
              suffix: metrics?.max_drawdown !== undefined ? '%' : '--',
              precision: 2,
            }}
            style={{ marginBottom: 16 }}
          />
        </Col>
        <Col span={12}>
          <StatisticCard
            statistic={{
              title: '年化波动率',
              value: metrics?.volatility,
              suffix: metrics?.volatility !== undefined ? '%' : '--',
              precision: 2,
            }}
            style={{ marginBottom: 16 }}
          />
        </Col>
        <Col span={12}>
          <StatisticCard
            statistic={{
              title: '回撤修复天数',
              value: metrics?.drawdown_recovery_days,
              suffix: metrics?.drawdown_recovery_days !== undefined ? '天' : '--',
            }}
            style={{ marginBottom: 16 }}
          />
        </Col>
      </Row>

      {metricsStatus === 'insufficient_data' && (
        <Alert
          message="数据不足"
          description="有效估值点不足2周，无法计算指标"
          type="info"
          showIcon
        />
      )}
      {metricsStatus === 'degraded' && (
        <Alert
          message="指标降级"
          description={metricsDegradedReason || "窗口期内发生资金流动，收益指标仅供参考"}
          type="warning"
          showIcon
        />
      )}
      {(hasEvents || metricsStatus === 'degraded') && (
        <Alert
          message="风险提示"
          description="收益率受资金流入流出影响，仅供参考"
          type="warning"
          showIcon
          style={{ marginTop: 8 }}
        />
      )}
    </>
  );
};

export default MetricsPanel;
