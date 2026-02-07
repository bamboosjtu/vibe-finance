import React from 'react';
import { Card, Timeline, Statistic, Row, Col, Tag, Tooltip, Empty, Alert } from 'antd';
import { 
  ClockCircleOutlined, 
  WalletOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';
import { CashTimelineResp } from '@/services/dashboard';
import dayjs from 'dayjs';

interface CashTimelineProps {
  data: CashTimelineResp | null;
  loading?: boolean;
}

const CashTimelineView: React.FC<CashTimelineProps> = ({ data, loading }) => {
  if (!data) {
    return (
      <Card title="资金时间视图" loading={loading}>
        <Empty description="暂无资金时间数据" />
      </Card>
    );
  }

  const { current, milestones } = data;

  // 构建时间轴节点
  const timelineItems = [
    // 当前状态节点
    {
      dot: <ClockCircleOutlined style={{ fontSize: '16px', color: '#1890ff' }} />,
      children: (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
            当前 ({dayjs(current.date).format('MM-DD')})
          </div>
          <Row gutter={[16, 8]}>
            <Col span={8}>
              <Statistic
                title="可用现金"
                value={current.available_cash}
                precision={2}
                prefix="￥"
                valueStyle={{ color: '#52c41a', fontSize: 16 }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="在途赎回"
                value={current.pending_redeems}
                precision={2}
                prefix="￥"
                valueStyle={{ color: '#faad14', fontSize: 16 }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="锁定资金"
                value={current.locked_in_products}
                precision={2}
                prefix="￥"
                valueStyle={{ color: '#999', fontSize: 16 }}
              />
            </Col>
          </Row>
        </div>
      ),
    },
    // 里程碑节点
    ...milestones.map((milestone) => ({
      dot: <ArrowRightOutlined style={{ fontSize: '14px', color: '#52c41a' }} />,
      children: (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
            {milestone.label} ({dayjs(milestone.date).format('MM-DD')})
            <Tag color="blue" style={{ marginLeft: 8 }}>
              预计可用 ￥{milestone.projected_available_cash.toFixed(0)}
            </Tag>
          </div>
          
          {milestone.changes.length > 0 ? (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                期间预计到账:
              </div>
              {milestone.changes.map((change, idx) => (
                <div 
                  key={idx} 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 8,
                    padding: '4px 0',
                    borderBottom: idx < milestone.changes.length - 1 ? '1px dashed #eee' : 'none'
                  }}
                >
                  <Tag color={change.source === 'redeem' ? 'blue' : 'green'}>
                    {change.source === 'redeem' ? '赎回' : '到期'}
                  </Tag>
                  <span style={{ color: '#52c41a', fontWeight: 500 }}>
                    +￥{change.amount.toFixed(0)}
                  </span>
                  <Tooltip title={change.description}>
                    <span style={{ 
                      color: '#666', 
                      fontSize: 12, 
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {change.description}
                    </span>
                  </Tooltip>
                  {change.note && (
                    <Tag style={{ fontSize: 10 }}>
                      {change.note}
                    </Tag>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#999', fontSize: 12 }}>
              该期间暂无已知到账预测
            </div>
          )}
        </div>
      ),
    })),
  ];

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <WalletOutlined />
          <span>资金时间视图</span>
          <Tooltip title="基于已知规则（赎回到账日、产品到期日）推算，仅供参考">
            <Tag color="warning">预计</Tag>
          </Tooltip>
        </div>
      }
      loading={loading}
    >
      <Alert
        message="时间维度说明"
        description="展示从当前时间点开始的资金流动性变化。'预计'表示基于规则推算，实际到账时间可能有偏差。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Timeline items={timelineItems} />
    </Card>
  );
};

export default CashTimelineView;
