import React, { useState, useEffect } from 'react';
import { PageContainer, ProCard, StatisticCard } from '@ant-design/pro-components';
import { DatePicker, Row, Col, Empty, Spin, Alert, Typography, Table, Tag, Tooltip, Button, Badge } from 'antd';
import { Pie } from '@ant-design/plots';
import { history } from '@umijs/max';
import { 
  getDashboardSummary, 
  getLatestSnapshotDate, 
  getAvailableDates, 
  DashboardSummary,
  getPendingRedeems,
  getFutureCashFlow,
  getCashTimeline,
  PendingRedeemItem,
  FutureCashFlowItem,
  CashTimelineResp
} from '@/services/dashboard';
import { getReconciliationWarnings, ReconciliationSummary } from '@/services/reconciliation';
import CashTimelineView from './components/CashTimeline';
import dayjs, { Dayjs } from 'dayjs';

const { Text, Title } = Typography;

const Dashboard: React.FC = () => {
  const [date, setDate] = useState<Dayjs>(dayjs());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [reconciliationSummary, setReconciliationSummary] = useState<ReconciliationSummary | null>(null);
  
  // Sprint 4: 新增状态
  const [pendingRedeems, setPendingRedeems] = useState<PendingRedeemItem[]>([]);
  const [futureCashFlow, setFutureCashFlow] = useState<FutureCashFlowItem[]>([]);
  const [cashFlowLoading, setCashFlowLoading] = useState(false);
  
  // Sprint 5: 新增状态
  const [cashTimeline, setCashTimeline] = useState<CashTimelineResp | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);

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
      setReconciliationSummary(resp.summary);
    } catch (e) {
      console.error('Failed to load reconciliation warnings:', e);
      setReconciliationSummary(null);
    }
  };

  // Sprint 4: 加载在途赎回数据
  const loadPendingRedeems = async () => {
    try {
      const resp = await getPendingRedeems();
      setPendingRedeems(resp.items);
    } catch (e) {
      console.error('Failed to load pending redeems:', e);
      setPendingRedeems([]);
    }
  };

  // Sprint 4: 加载未来现金流
  const loadFutureCashFlow = async () => {
    setCashFlowLoading(true);
    try {
      const resp = await getFutureCashFlow(30);
      setFutureCashFlow(resp.items);
    } catch (e) {
      console.error('Failed to load future cash flow:', e);
      setFutureCashFlow([]);
    } finally {
      setCashFlowLoading(false);
    }
  };

  // Sprint 5: 加载资金时间轴
  const loadCashTimeline = async () => {
    setTimelineLoading(true);
    try {
      const resp = await getCashTimeline('7,30,90');
      setCashTimeline(resp);
      // 90天预测现在统一从 DashboardSummary 获取，不再从时间轴计算
    } catch (e) {
      console.error('Failed to load cash timeline:', e);
      setCashTimeline(null);
    } finally {
      setTimelineLoading(false);
    }
  };

  useEffect(() => {
    loadLatestDate();
    loadAvailableDates();
    loadReconciliationWarnings();
    loadPendingRedeems();
    loadFutureCashFlow();
    loadCashTimeline();
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

  // Sprint 4: 在途赎回表格列定义
  const pendingRedeemColumns = [
    {
      title: '产品',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '在途金额',
      dataIndex: 'pending_amount',
      key: 'pending_amount',
      render: (amount: number) => `￥${amount.toFixed(2)}`,
    },
    {
      title: '申请日期',
      dataIndex: 'latest_request_date',
      key: 'latest_request_date',
      render: (date: string | null) => date || '-',
    },
    {
      title: '预计到账',
      dataIndex: 'estimated_settle_date',
      key: 'estimated_settle_date',
      render: (date: string | null) => date ? (
        <Tag color="blue">{date}</Tag>
      ) : (
        <Tag>待定</Tag>
      ),
    },
  ];

  // Sprint 4: 未来现金流表格列定义
  const cashFlowColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => dayjs(date).format('MM-DD'),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          +￥{amount.toFixed(2)}
        </span>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      render: (source: string) => (
        <Tag color={source === 'redeem' ? 'blue' : 'green'}>
          {source === 'redeem' ? '赎回' : '到期'}
        </Tag>
      ),
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '备注',
      dataIndex: 'note',
      key: 'note',
      render: (note: string | undefined) => note ? (
        <Text type="secondary" style={{ fontSize: 12 }}>{note}</Text>
      ) : null,
    },
  ];

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
              {/* 第一行：核心资产指标 */}
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
                      title: '基础可用现金',
                      value: summary.available_cash,
                      precision: 2,
                      suffix: '元',
                    }}
                  />
                </Col>
              </Row>

              {/* Sprint 4: 第二行 - 现金可用性指标 */}
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={6}>
                  <Tooltip title="已扣除赎回在途资金，反映真实可动用现金">
                    <StatisticCard
                      statistic={{
                        title: '实际可用现金',
                        value: summary.real_available_cash,
                        precision: 2,
                        suffix: '元',
                        valueStyle: { color: '#52c41a', fontWeight: 'bold' },
                      }}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="已发起赎回但尚未到账的资金">
                    <StatisticCard
                      statistic={{
                        title: '赎回在途',
                        value: summary.pending_redeems,
                        precision: 2,
                        suffix: '元',
                        valueStyle: { color: '#faad14' },
                      }}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="未来7天内预计到账的资金（规则推算）">
                    <StatisticCard
                      statistic={{
                        title: '未来7天预计到账',
                        value: summary.future_7d,
                        precision: 2,
                        suffix: '元',
                        valueStyle: { color: '#1890ff' },
                      }}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="未来30天内预计到账的资金（规则推算）">
                    <StatisticCard
                      statistic={{
                        title: '未来30天预计到账',
                        value: summary.future_30d,
                        precision: 2,
                        suffix: '元',
                        valueStyle: { color: '#1890ff' },
                      }}
                    />
                  </Tooltip>
                </Col>
              </Row>

              {/* Sprint 5: 第三行 - 扩展预测区间 */}
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={6}>
                  <Tooltip title="未来90天内预计到账的资金（规则推算）">
                    <StatisticCard
                      statistic={{
                        title: '未来90天预计到账',
                        value: summary?.future_90d || 0,
                        precision: 2,
                        suffix: '元',
                        valueStyle: { color: '#722ed1' },
                      }}
                    />
                  </Tooltip>
                </Col>
                <Col span={18}>
                  <Alert
                    message="资金预测说明"
                    description="未来资金到账基于已录入的赎回申请和产品到期日规则推算，实际到账时间可能因节假日、银行处理等因素有所偏差。"
                    type="info"
                    showIcon
                  />
                </Col>
              </Row>

              {/* Sprint 5: 资金时间轴视图 */}
              <CashTimelineView 
                data={cashTimeline} 
                loading={timelineLoading} 
              />

              {/* 资产结构图表 */}
              <ProCard title="资产结构" bordered style={{ marginTop: 16 }}>
                {pieData.length > 0 ? (
                  <Pie {...pieConfig} height={300} />
                ) : (
                  <Empty description="暂无资产数据" />
                )}
              </ProCard>

              {/* Sprint 4: 在途赎回明细 */}
              {pendingRedeems.length > 0 && (
                <ProCard 
                  title="赎回在途明细" 
                  bordered 
                  style={{ marginTop: 16 }}
                  extra={<Tag color="warning">{pendingRedeems.length} 笔在途</Tag>}
                >
                  <Table
                    dataSource={pendingRedeems}
                    columns={pendingRedeemColumns}
                    rowKey="product_id"
                    pagination={false}
                    size="small"
                  />
                </ProCard>
              )}

              {/* Sprint 4: 未来现金流预测 */}
              <Spin spinning={cashFlowLoading}>
                {futureCashFlow.length > 0 && (
                  <ProCard 
                    title="未来资金到账预测" 
                    bordered 
                    style={{ marginTop: 16 }}
                    extra={
                      <Tooltip title="基于产品T+N规则和已录入的赎回申请推算，仅供参考">
                        <Text type="secondary" style={{ fontSize: 12 }}>规则推算，仅供参考</Text>
                      </Tooltip>
                    }
                  >
                    <Table
                      dataSource={futureCashFlow.slice(0, 10)}
                      columns={cashFlowColumns}
                      rowKey={(record) => `${record.date}-${record.product_id}`}
                      pagination={futureCashFlow.length > 10 ? { pageSize: 10 } : false}
                      size="small"
                    />
                    {futureCashFlow.length > 10 && (
                      <Text type="secondary" style={{ display: 'block', marginTop: 8, textAlign: 'center' }}>
                        还有 {futureCashFlow.length - 10} 笔待到账...
                      </Text>
                    )}
                  </ProCard>
                )}
              </Spin>

              {/* Sprint 6: 对账提醒入口 */}
              {reconciliationSummary && reconciliationSummary.total > 0 && (
                <ProCard 
                  title={
                    <span>
                      对账提醒
                      <Badge 
                        count={reconciliationSummary.warn} 
                        style={{ marginLeft: 8, backgroundColor: '#ff4d4f' }}
                      />
                    </span>
                  }
                  bordered 
                  style={{ marginTop: 16 }}
                  extra={
                    <Button 
                      type="primary" 
                      size="small"
                      onClick={() => history.push('/reconciliation')}
                    >
                      查看全部
                    </Button>
                  }
                >
                  <Row gutter={16}>
                    <Col>
                      <Text type="danger" strong>
                        {reconciliationSummary.warn} 个警告
                      </Text>
                    </Col>
                    <Col>
                      <Text type="secondary">
                        {reconciliationSummary.info} 个提示
                      </Text>
                    </Col>
                  </Row>
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
