import React, { useState, useEffect } from 'react';
import { useParams, history } from '@umijs/max';
import { PageContainer, ProCard } from '@ant-design/pro-components';
import { Radio, Descriptions, Tag, Row, Col } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useProductDetail } from './hooks/useProductDetail';
import ProductChart from './components/ProductChart';
import MetricsPanel from './components/MetricsPanel';
import ValuationTable from './components/ValuationTable';
import TransactionTable from './components/TransactionTable';

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

  // 同步估值数据到本地状态
  useEffect(() => {
    setValuationData(valuationDataSource);
  }, [valuationDataSource]);

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
