import React, { useState, useEffect } from 'react';
import { PageContainer, ProCard, StatisticCard } from '@ant-design/pro-components';
import { DatePicker, Row, Col, Empty, Spin, Alert, Typography } from 'antd';
import { Pie } from '@ant-design/plots';
import { getDashboardSummary, getLatestSnapshotDate, getAvailableDates, DashboardSummary } from '@/services/dashboard';
import { getReconciliationWarnings } from '@/services/reconciliation';
import dayjs, { Dayjs } from 'dayjs';

const { Text } = Typography;

const Dashboard: React.FC = () => {
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [reconciliationNote, setReconciliationNote] = useState<string | undefined>(undefined);

  const loadSummary = async (targetDate: Dayjs) => {
    setLoading(true);
    try {
      const resp = await getDashboardSummary(targetDate.format('YYYY-MM-DD'));
      setSummary(resp);
      setHasData(true);
    } catch (e) {
      console.error('Failed to load dashboard summary:', e);
      setSummary(null);
      setHasData(false);
    } finally {
      setLoading(false);
    }
  };

  const loadLatestDate = async () => {
    try {
      const resp = await getLatestSnapshotDate();
      if (resp.date) {
        setDate(dayjs(resp.date));
        await loadSummary(dayjs(resp.date));
      } else {
        setHasData(false);
        setSummary(null);
      }
    } catch (e) {
      console.error('Failed to load latest snapshot date:', e);
      setHasData(false);
      setSummary(null);
    }
  };

  const loadAvailableDates = async () => {
    try {
      const resp = await getAvailableDates();
      setAvailableDates(resp.dates);
    } catch (e) {
      console.error('Failed to load available dates:', e);
      setAvailableDates([]);
    }
  };

  const loadReconciliationWarnings = async () => {
    try {
      const resp = await getReconciliationWarnings();
      setReconciliationNote(resp.note);
    } catch (e) {
      console.error('Failed to load reconciliation warnings:', e);
      setReconciliationNote(undefined);
    }
  };

  useEffect(() => {
    loadLatestDate();
    loadAvailableDates();
    loadReconciliationWarnings();
  }, []);

  const handleDateChange = async (newDate: Dayjs | null) => {
    if (newDate) {
      setDate(newDate);
      await loadSummary(newDate);
    }
  };

  const disabledDate = (current: Dayjs) => {
    const dateStr = current.format('YYYY-MM-DD');
    return !availableDates.includes(dateStr);
  };

  const pieData = summary ? [
    { type: '现金', value: summary.by_type.cash / 10000 },
    { type: '借记卡', value: summary.by_type.debit / 10000 },
    { type: '信用卡', value: Math.abs(summary.by_type.credit) / 10000 },
    { type: '投资账户', value: summary.by_type.investment_cash / 10000 },
    { type: '其他', value: summary.by_type.other / 10000 },
  ].filter(item => item.value !== 0) : [];

  interface PieDataItem {
    type: string;
    value: number;
  }

  const pieConfig = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    innerRadius: 0.3,
    label: {
      position: 'spider',
      text: (d: PieDataItem) => `${d.type}：￥${d.value.toFixed(2)}万元`,
      transform: [{ type: 'overlapDodgeY' }],
    },
    tooltip: {
      items: [
        (d: PieDataItem) => ({ name: d.type, value: `￥${d.value.toFixed(2)}万元` }),
      ],
    },
  };

  return (
    <PageContainer
      header={{
        title: '资产概览',
      }}
    >
      <Spin spinning={loading}>
        <ProCard direction="column" ghost gutter={[0, 16]}>
          {!hasData ? (
            <Alert
              message="暂无资产快照数据，请先在资产快照页面录入数据"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          ) : null}

          <Row gutter={16}>
            <Col span={6}>
              <DatePicker
                value={date}
                onChange={handleDateChange}
                disabledDate={disabledDate}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>

          {summary ? (
            <>
              <Row gutter={16}>
                <Col span={6}>
                  <StatisticCard
                    statistic={{
                      title: '总资产',
                      value: summary.total_assets,
                      precision: 2,
                      suffix: '元',
                    }}
                  />
                </Col>
                <Col span={6}>
                  <StatisticCard
                    statistic={{
                      title: '流动资产',
                      value: summary.liquid_assets,
                      precision: 2,
                      suffix: '元',
                    }}
                  />
                </Col>
                <Col span={6}>
                  <StatisticCard
                    statistic={{
                      title: '负债',
                      value: Math.abs(summary.liabilities),
                      precision: 2,
                      suffix: '元',
                      valueStyle: { color: 'red' },
                    }}
                  />
                </Col>
                <Col span={6}>
                  <StatisticCard
                    statistic={{
                      title: '可用现金',
                      value: summary.available_cash,
                      precision: 2,
                      suffix: '元',
                      valueStyle: { color: summary.available_cash > 0 ? 'green' : 'red' },
                    }}
                  />
                </Col>
              </Row>

              <ProCard title="资产结构" bordered>
                {pieData.length > 0 ? (
                  <Pie {...pieConfig} height={300} />
                ) : (
                  <Empty description="暂无资产数据" />
                )}
              </ProCard>

              {reconciliationNote && (
                <ProCard bordered style={{ marginTop: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    ℹ️ {reconciliationNote}
                  </Text>
                </ProCard>
              )}
            </>
          ) : null}
        </ProCard>
      </Spin>
    </PageContainer>
  );
};

export default Dashboard;
