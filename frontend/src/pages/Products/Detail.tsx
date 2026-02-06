import React, { useState, useEffect } from 'react';
import { useParams, history } from '@umijs/max';
import { PageContainer, ProCard } from '@ant-design/pro-components';
import { Radio, Descriptions, Tag, Row, Col, Alert, Statistic } from 'antd';
import { ArrowLeftOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useProductDetail } from './hooks/useProductDetail';
import ProductChart from './components/ProductChart';
import MetricsPanel from './components/MetricsPanel';
import ValuationTable from './components/ValuationTable';
import TransactionTable from './components/TransactionTable';
import { getProductPendingRedeem, ProductPendingRedeemResp } from '@/services/products';

const { Item: DescItem } = Descriptions;

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const productId = Number(id);

  const {
    product,
    accounts,
    window,
    setWindow,
    metrics,
    metricsStatus,
    metricsDegradedReason,
    chartData,
    events,
    xMin,
    xMax,
    yMin,
    yMax,
    transactions,
    valuationDataSource,
    refresh,
  } = useProductDetail(productId);

  // 估值表格本地状态
  const [valuationData, setValuationData] = useState<readonly any[]>([]);

  // Sprint 4: 在途赎回状态
  const [pendingRedeem, setPendingRedeem] = useState<ProductPendingRedeemResp | null>(null);
  const [pendingRedeemLoading, setPendingRedeemLoading] = useState(false);

  // 同步估值数据到本地状态
  useEffect(() => {
    setValuationData(valuationDataSource);
  }, [valuationDataSource]);

  // Sprint 4: 加载在途赎回信息
  useEffect(() => {
    const loadPendingRedeem = async () => {
      setPendingRedeemLoading(true);
      try {
        const resp = await getProductPendingRedeem(productId);
        setPendingRedeem(resp);
      } catch (e) {
        console.error('Failed to load pending redeem:', e);
        setPendingRedeem(null);
      } finally {
        setPendingRedeemLoading(false);
      }
    };

    if (productId) {
      loadPendingRedeem();
    }
  }, [productId, transactions]); // 交易记录变化时重新加载

  return (
    <PageContainer
      header={{
        title: product?.name || '产品详情',
        subTitle: product?.institution_id ? undefined : '无机构',
        tags: product?.risk_level ? <Tag color="blue">{product.risk_level}</Tag> : undefined,
        backIcon: <ArrowLeftOutlined />,
        onBack: () => history.push('/master/products'),
      }}
    >
      {/* 产品规则区 */}
      <ProCard title="产品规则" headerBordered style={{ marginBottom: 16 }}>
        <Descriptions column={4}>
          <DescItem label="产品类型">{product?.product_type}</DescItem>
          <DescItem label="期限">{product?.term_days ? `${product.term_days}天` : '-'}</DescItem>
          <DescItem label="赎回到账">T+{product?.settle_days || 1}</DescItem>
          <DescItem label="流动性">{product?.liquidity_rule === 'open' ? '开放' : product?.liquidity_rule === 'closed' ? '封闭' : '定开'}</DescItem>
        </Descriptions>
      </ProCard>

      {/* Sprint 4: 在途赎回信息区（仅在有时显示） */}
      {pendingRedeem && pendingRedeem.pending_amount > 0 && (
        <Alert
          message={
            <Row gutter={24} align="middle">
              <Col>
                <Statistic
                  title="赎回在途金额"
                  value={pendingRedeem.pending_amount}
                  precision={2}
                  prefix="￥"
                  valueStyle={{ color: '#faad14', fontWeight: 'bold' }}
                />
              </Col>
              <Col>
                <div style={{ fontSize: 14 }}>
                  <ClockCircleOutlined style={{ marginRight: 8 }} />
                  最近申请: {pendingRedeem.latest_request_date || '-'}
                </div>
              </Col>
              <Col>
                <div style={{ fontSize: 14 }}>
                  <ClockCircleOutlined style={{ marginRight: 8 }} />
                  预计到账: {pendingRedeem.estimated_settle_date ? (
                    <Tag color="blue">{pendingRedeem.estimated_settle_date}</Tag>
                  ) : (
                    <Tag>T+{product?.settle_days || 1} 推算</Tag>
                  )}
                </div>
              </Col>
            </Row>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 走势展示区 */}
      <ProCard
        title="市值走势"
        headerBordered
        style={{ marginBottom: 16 }}
        extra={
          <Radio.Group value={window} onChange={e => setWindow(e.target.value)}>
            <Radio.Button value="4w">4周</Radio.Button>
            <Radio.Button value="8w">8周</Radio.Button>
            <Radio.Button value="12w">12周</Radio.Button>
            <Radio.Button value="24w">24周</Radio.Button>
            <Radio.Button value="1y">1年</Radio.Button>
            <Radio.Button value="ytd">YTD</Radio.Button>
          </Radio.Group>
        }
      >
        <Row gutter={8}>
          <Col span={17}>
            <ProductChart
              chartData={chartData}
              events={events}
              xMin={xMin}
              xMax={xMax}
              yMin={yMin}
              yMax={yMax}
            />
          </Col>
          <Col span={4}>
            <MetricsPanel
              metrics={metrics}
              metricsStatus={metricsStatus}
              metricsDegradedReason={metricsDegradedReason}
              hasEvents={events.length > 0}
            />
          </Col>
          <Col span={3}>
            {/* 右侧留白或放置其他内容 */}
          </Col>
        </Row>
      </ProCard>

      {/* 记录区 */}
      <ProCard split="vertical">
        <ProCard title="估值录入" colSpan="50%" headerBordered>
          <ValuationTable
            productId={productId}
            dataSource={valuationData as any[]}
            onChange={setValuationData}
            onRefresh={refresh}
          />
        </ProCard>

        <ProCard title="交易记录" colSpan="50%" headerBordered>
          <TransactionTable
            productId={productId}
            accounts={accounts}
            dataSource={transactions}
            onRefresh={refresh}
          />
        </ProCard>
      </ProCard>
    </PageContainer>
  );
};

export default ProductDetail;
