import React, { useState, useEffect } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Card, Table, Tag, Badge, Alert, Button, DatePicker, Radio, Space, Typography, Empty, Dropdown, Modal, Input, message, Tooltip } from 'antd';
import { history } from '@umijs/max';
import dayjs from 'dayjs';
import {
  WarningOutlined,
  InfoCircleOutlined,
  BankOutlined,
  FundOutlined,
  LineChartOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  BellOutlined,
  MoreOutlined,
  UndoOutlined,
} from '@ant-design/icons';
import {
  getReconciliationWarnings,
  updateWarningStatus,
  restoreWarning,
  ReconciliationWarning,
  ReconciliationSummary,
} from '@/services/reconciliation';

const { Text, Title } = Typography;

const ReconciliationCenter: React.FC = () => {
  const [warnings, setWarnings] = useState<ReconciliationWarning[]>([]);
  const [summary, setSummary] = useState<ReconciliationSummary>({ total: 0, warn: 0, info: 0 });
  const [loading, setLoading] = useState(false);
  const [checkDate, setCheckDate] = useState<dayjs.Dayjs>(dayjs());
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('open');

  // S6-5: Mute 对话框
  const [muteModalVisible, setMuteModalVisible] = useState(false);
  const [muteReason, setMuteReason] = useState('');
  const [currentWarning, setCurrentWarning] = useState<ReconciliationWarning | null>(null);

  // 加载对账警告
  const loadWarnings = async (targetDate?: dayjs.Dayjs) => {
    setLoading(true);
    try {
      const date = targetDate || checkDate;
      const resp = await getReconciliationWarnings(date.format('YYYY-MM-DD'));
      setWarnings(resp.items);
      setSummary(resp.summary);
    } catch (e) {
      console.error('Failed to load reconciliation warnings:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWarnings();
  }, []);

  // S6-5: 更新警告状态
  const handleUpdateStatus = async (warning: ReconciliationWarning, status: 'open' | 'acknowledged' | 'muted') => {
    try {
      if (status === 'muted') {
        setCurrentWarning(warning);
        setMuteModalVisible(true);
        return;
      }

      await updateWarningStatus(warning.id, status);
      message.success(status === 'acknowledged' ? '已确认' : '已恢复');
      loadWarnings();
    } catch (e) {
      console.error('Failed to update warning status:', e);
      message.error('操作失败');
    }
  };

  // S6-5: 提交 Mute 原因
  const handleMuteSubmit = async () => {
    if (!currentWarning) return;

    try {
      await updateWarningStatus(currentWarning.id, 'muted', muteReason);
      message.success('已静音');
      setMuteModalVisible(false);
      setMuteReason('');
      setCurrentWarning(null);
      loadWarnings();
    } catch (e) {
      console.error('Failed to mute warning:', e);
      message.error('操作失败');
    }
  };

  // S6-5: 恢复警告
  const handleRestore = async (warning: ReconciliationWarning) => {
    try {
      await restoreWarning(warning.id);
      message.success('已恢复为未处理');
      loadWarnings();
    } catch (e) {
      console.error('Failed to restore warning:', e);
      message.error('操作失败');
    }
  };

  // 过滤后的警告列表
  const filteredWarnings = warnings.filter((w) => {
    // 类型过滤
    if (filterType === 'all') {
      // 显示所有
    } else if (filterType === 'warn') {
      if (w.level !== 'warn') return false;
    } else if (filterType === 'info') {
      if (w.level !== 'info') return false;
    } else {
      if (w.type !== filterType) return false;
    }

    // 状态过滤
    if (filterStatus === 'open') {
      if (w.status !== 'open') return false;
    } else if (filterStatus === 'acknowledged') {
      if (w.status !== 'acknowledged') return false;
    } else if (filterStatus === 'muted') {
      if (w.status !== 'muted') return false;
    }

    return true;
  });

  // 状态标签渲染
  const renderStatusTag = (status: string, muteReason?: string | null) => {
    switch (status) {
      case 'open':
        return <Tag color="default">未处理</Tag>;
      case 'acknowledged':
        return <Tag color="blue" icon={<CheckCircleOutlined />}>已确认</Tag>;
      case 'muted':
        return (
          <Tooltip title={muteReason || '已知差异'}>
            <Tag color="orange" icon={<BellOutlined />}>已静音</Tag>
          </Tooltip>
        );
      default:
        return <Tag>{status}</Tag>;
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '级别',
      dataIndex: 'level',
      width: 120,
      render: (level: string) => (
        <Badge
          status={level === 'warn' ? 'error' : 'default'}
          text={
            level === 'warn' ? (
              <Tag color="error" icon={<WarningOutlined />}>
                警告
              </Tag>
            ) : (
              <Tag color="default" icon={<InfoCircleOutlined />}>
                提示
              </Tag>
            )
          }
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: string, record: ReconciliationWarning) => renderStatusTag(status, record.mute_reason),
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: 120,
      render: (type: string) => {
        const typeMap: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
          account_diff: { label: '账户对账', icon: <BankOutlined />, color: 'blue' },
          redeem_anomaly: { label: '赎回异常', icon: <FundOutlined />, color: 'orange' },
          valuation_gap: { label: '估值断档', icon: <LineChartOutlined />, color: 'purple' },
        };
        const config = typeMap[type] || { label: type, icon: null, color: 'default' };
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: '对象',
      dataIndex: 'object_name',
      render: (_: string, record: ReconciliationWarning) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.object_name}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.object_type === 'account' ? '账户' : '产品'}
          </Text>
        </Space>
      ),
    },
    {
      title: '问题描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (desc: string, record: ReconciliationWarning) => (
        <Space direction="vertical" size={0} style={{ maxWidth: 400 }}>
          <Text strong>{record.title}</Text>
          <Text type="secondary" ellipsis style={{ fontSize: 12 }}>
            {desc}
          </Text>
        </Space>
      ),
    },
    {
      title: '差异值',
      dataIndex: 'diff_value',
      width: 120,
      align: 'right' as const,
      render: (val: number | null) =>
        val !== null ? (
          <Text type={val > 0 ? 'success' : 'danger'}>
            {val > 0 ? '+' : ''}
            {val.toFixed(2)}
          </Text>
        ) : (
          '-'
        ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: ReconciliationWarning) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<ArrowRightOutlined />}
            onClick={() => history.push(record.link_to)}
          >
            查看
          </Button>
          <Dropdown
            menu={{
              items: [
                ...(record.status === 'open' ? [
                  {
                    key: 'acknowledge',
                    label: '确认已知晓',
                    icon: <CheckCircleOutlined />,
                    onClick: () => handleUpdateStatus(record, 'acknowledged'),
                  },
                  {
                    key: 'mute',
                    label: '静音（已知差异）',
                    icon: <BellOutlined />,
                    onClick: () => handleUpdateStatus(record, 'muted'),
                  },
                ] : []),
                ...(record.status !== 'open' ? [
                  {
                    key: 'restore',
                    label: '恢复为未处理',
                    icon: <UndoOutlined />,
                    onClick: () => handleRestore(record),
                  },
                ] : []),
              ],
            }}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  // 计算各状态数量
  const statusCounts = {
    all: warnings.length,
    open: warnings.filter(w => w.status === 'open').length,
    acknowledged: warnings.filter(w => w.status === 'acknowledged').length,
    muted: warnings.filter(w => w.status === 'muted').length,
  };

  return (
    <PageContainer
      header={{
        title: '对账中心',
        subTitle: '发现数据不一致，帮助快速补录/纠错',
      }}
    >
      {/* 统计卡片 */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="large">
          <div>
            <Text type="secondary">待处理警告</Text>
            <div>
              <Title level={3} style={{ margin: 0, color: '#ff4d4f' }}>
                {summary.warn}
              </Title>
            </div>
          </div>
          <div>
            <Text type="secondary">提示信息</Text>
            <div>
              <Title level={3} style={{ margin: 0, color: '#8c8c8c' }}>
                {summary.info}
              </Title>
            </div>
          </div>
          <div>
            <Text type="secondary">总计</Text>
            <div>
              <Title level={3} style={{ margin: 0 }}>
                {summary.total}
              </Title>
            </div>
          </div>
        </Space>
      </Card>

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <DatePicker
            value={checkDate}
            onChange={(date) => {
              if (date) {
                setCheckDate(date);
                loadWarnings(date);
              }
            }}
          />
          <Radio.Group value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <Radio.Button value="all">全部</Radio.Button>
            <Radio.Button value="warn">仅警告</Radio.Button>
            <Radio.Button value="info">仅提示</Radio.Button>
            <Radio.Button value="account_diff">账户对账</Radio.Button>
            <Radio.Button value="redeem_anomaly">赎回异常</Radio.Button>
            <Radio.Button value="valuation_gap">估值断档</Radio.Button>
          </Radio.Group>
          <Radio.Group value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <Radio.Button value="all">全部状态 ({statusCounts.all})</Radio.Button>
            <Radio.Button value="open">未处理 ({statusCounts.open})</Radio.Button>
            <Radio.Button value="acknowledged">已确认 ({statusCounts.acknowledged})</Radio.Button>
            <Radio.Button value="muted">已静音 ({statusCounts.muted})</Radio.Button>
          </Radio.Group>
          <Button type="primary" onClick={() => loadWarnings()} loading={loading}>
            刷新
          </Button>
        </Space>
      </Card>

      {/* 说明 */}
      <Alert
        message="对账口径说明"
        description="Snapshot 是最高权威，系统不修正 Snapshot，只做提示与定位。差异可能原因：漏录交易、交易 settle_date 填错、账户选错、Snapshot 录错等。已静音的警告可随时恢复。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* 警告列表 */}
      <Card title="对账警告列表">
        {filteredWarnings.length === 0 ? (
          <Empty description="暂无对账警告" />
        ) : (
          <Table
            dataSource={filteredWarnings}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>

      {/* S6-5: Mute 原因对话框 */}
      <Modal
        title="静音原因（可选）"
        open={muteModalVisible}
        onOk={handleMuteSubmit}
        onCancel={() => {
          setMuteModalVisible(false);
          setMuteReason('');
          setCurrentWarning(null);
        }}
      >
        <p>将此警告静音后，它将不再显示在"未处理"列表中，但可随时恢复。</p>
        <Input.TextArea
          placeholder="请输入静音原因（如：已知差异，待后续处理）"
          value={muteReason}
          onChange={(e) => setMuteReason(e.target.value)}
          rows={3}
        />
      </Modal>
    </PageContainer>
  );
};

export default ReconciliationCenter;
