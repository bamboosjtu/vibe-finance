import React, { useState, useEffect } from 'react';
import { useParams, history } from '@umijs/max';
import { PageContainer, ProCard } from '@ant-design/pro-components';
import { Radio, Descriptions, Tag, Row, Col, Alert, Statistic } from 'antd';
import { ArrowLeftOutlined, ClockCircleOutlined, LockOutlined, UnlockOutlined, WarningOutlined, LineChartOutlined } from '@ant-design/icons';
import { useProductDetail } from './hooks/useProductDetail';
import ProductChart from './components/ProductChart';
import MetricsPanel from './components/MetricsPanel';
import ValuationTable from './components/ValuationTable';
import TransactionTable from './components/TransactionTable';
import { 
  getProductPendingRedeem, 
  ProductPendingRedeemResp,
  getProductLiquidityStatus,
  ProductLiquidityStatusResp
} from '@/services/products';
import { getRedeemCheck, getValuationGaps, RedeemCheckItem, ValuationGapItem } from '@/services/reconciliation';

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

  // Sprint 5: 流动性状态
  const [liquidityStatus, setLiquidityStatus] = useState<ProductLiquidityStatusResp | null>(null);
  const [liquidityLoading, setLiquidityLoading] = useState(false);

  // Sprint 6: 赎回异常检查
  const [redeemCheck, setRedeemCheck] = useState<RedeemCheckItem | null>(null);
  const [redeemCheckLoading, setRedeemCheckLoading] = useState(false);

  // Sprint 6: 估值断档检查
  const [valuationGap, setValuationGap] = useState<ValuationGapItem | null>(null);
  const [valuationGapLoading, setValuationGapLoading] = useState(false);

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

  // Sprint 5: 加载流动性状态
  useEffect(() => {
    const loadLiquidityStatus = async () => {
      setLiquidityLoading(true);
      try {
        const resp = await getProductLiquidityStatus(productId);
        setLiquidityStatus(resp);
      } catch (e) {
        console.error('Failed to load liquidity status:', e);
        // 即使 API 失败，也尝试从 product 基本信息构建一个默认状态
        if (product) {
          setLiquidityStatus({
            product_id: productId,
            product_name: product.name,
            is_locked: false,
            lock_end_date: null,
            next_liquid_date: null,
            liquidity_type: product.liquidity_rule === 'open' ? 'open' : 
                           product.liquidity_rule === 'closed' ? 'closed' : 'periodic_open',
            term_days: product.term_days || 0,
            settle_days: product.settle_days || 1,
            note: product.liquidity_rule === 'open' ? '开放式产品，可随时赎回' :
                  product.liquidity_rule === 'closed' ? '封闭式产品，请查看到期日' :
                  '定期开放产品，请关注开放期'
          });
        } else {
          setLiquidityStatus(null);
        }
      } finally {
        setLiquidityLoading(false);
      }
    };

    if (productId) {
      loadLiquidityStatus();
    }
  }, [productId, product]);

  // Sprint 6: 加载赎回异常检查
  useEffect(() => {
    const loadRedeemCheck = async () => {
      setRedeemCheckLoading(true);
      try {
        const resp = await getRedeemCheck();
        // 找到当前产品的检查结果
        const productCheck = resp.items.find(item => item.product_id === productId);
        setRedeemCheck(productCheck || null);
      } catch (e) {
        console.error('Failed to load redeem check:', e);
        setRedeemCheck(null);
      } finally {
        setRedeemCheckLoading(false);
      }
    };

    if (productId) {
      loadRedeemCheck();
    }
  }, [productId, transactions]);

  // Sprint 6: 加载估值断档检查
  useEffect(() => {
    const loadValuationGap = async () => {
      setValuationGapLoading(true);
      try {
        const resp = await getValuationGaps();
        // 找到当前产品的断档信息
        const productGap = resp.items.find(item => item.product_id === productId);
        setValuationGap(productGap || null);
      } catch (e) {
        console.error('Failed to load valuation gap:', e);
        setValuationGap(null);
      } finally {
        setValuationGapLoading(false);
      }
    };

    if (productId) {
      loadValuationGap();
    }
  }, [productId, valuationDataSource]);

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

      {/* Sprint 5: 流动性状态提示 */}
      {liquidityStatus && (
        <Alert
          message={
            <Row gutter={24} align="middle">
              <Col>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {liquidityStatus.is_locked ? (
                    <LockOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
                  ) : (
                    <UnlockOutlined style={{ color: '#52c41a', fontSize: 18 }} />
                  )}
                  <span style={{ fontWeight: 'bold' }}>
                    {liquidityStatus.is_locked ? '锁定期中' : 
                     liquidityStatus.liquidity_type === 'open' ? '开放式' : 
                     liquidityStatus.liquidity_type === 'closed' ? '封闭式' : '定期开放'}
                  </span>
                </div>
              </Col>
              {liquidityStatus.is_locked && liquidityStatus.lock_end_date && (
                <Col>
                  <div style={{ fontSize: 14 }}>
                    <ClockCircleOutlined style={{ marginRight: 8 }} />
                    锁定期至: <Tag color="red">{liquidityStatus.lock_end_date}</Tag>
                  </div>
                </Col>
              )}
              {!liquidityStatus.is_locked && liquidityStatus.next_liquid_date && (
                <Col>
                  <div style={{ fontSize: 14 }}>
                    <ClockCircleOutlined style={{ marginRight: 8 }} />
                    最近可变现: <Tag color="blue">{liquidityStatus.next_liquid_date}</Tag>
                  </div>
                </Col>
              )}
              <Col>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {liquidityStatus.note}
                </div>
              </Col>
            </Row>
          }
          type={liquidityStatus.is_locked ? 'error' : 'success'}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

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

      {/* Sprint 6: 赎回异常提示 */}
      {redeemCheck && (redeemCheck.status === 'negative' || redeemCheck.status === 'overdue') && (
        <Alert
          message={
            <Row gutter={24} align="middle">
              <Col>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <WarningOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
                  <span style={{ fontWeight: 'bold' }}>
                    {redeemCheck.status === 'negative' ? '赎回金额异常' : '赎回到账逾期'}
                  </span>
                </div>
              </Col>
              <Col>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {redeemCheck.hint}
                </div>
              </Col>
              {redeemCheck.days_pending && (
                <Col>
                  <Tag color="red">已逾期 {redeemCheck.days_pending} 天</Tag>
                </Col>
              )}
            </Row>
          }
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Sprint 6: 估值断档提示 */}
      {valuationGap && (
        <Alert
          message={
            <Row gutter={24} align="middle">
              <Col>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <LineChartOutlined style={{ color: valuationGap.severity === 'warn' ? '#ff4d4f' : '#faad14', fontSize: 18 }} />
                  <span style={{ fontWeight: 'bold' }}>
                    估值断档
                  </span>
                </div>
              </Col>
              <Col>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {valuationGap.hint}
                </div>
              </Col>
              <Col>
                <Tag color={valuationGap.severity === 'warn' ? 'red' : 'orange'}>
                  {valuationGap.days_since > 999 ? '从未录入' : `${valuationGap.days_since} 天未更新`}
                </Tag>
              </Col>
              {valuationGap.has_recent_trade && (
                <Col>
                  <Tag color="blue">期间有交易</Tag>
                </Col>
              )}
              {/* Sprint 6 可选：显示最近一次交易日期 */}
              {valuationGap.last_trade_date && (
                <Col>
                  <Tag color="cyan">
                    最近交易: {valuationGap.days_since_trade} 天前
                  </Tag>
                </Col>
              )}
            </Row>
          }
          type={valuationGap.severity === 'warn' ? 'error' : 'warning'}
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
