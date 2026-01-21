import React, { useState, useEffect } from 'react';
import { useParams, history } from '@umijs/max';
import { PageContainer, ProCard, StatisticCard } from '@ant-design/pro-components';
import { Line } from '@ant-design/plots';
import { Radio, Descriptions, Tag, Alert, Empty, Button } from 'antd';
import { getProductMetrics, listProducts, Product, ProductMetrics } from '@/services/products';
import { getProductValuations, ProductValuation } from '@/services/valuations';
import dayjs from 'dayjs';

const ProductDetail: React.FC = () => {
  const params = useParams<{ id: string }>();
  const productId = Number(params.id);
  
  const [product, setProduct] = useState<Product | null>(null);
  const [metrics, setMetrics] = useState<ProductMetrics | null>(null);
  const [valuations, setValuations] = useState<ProductValuation[]>([]);
  const [loading, setLoading] = useState(false);
  const [window, setWindow] = useState('8w');
  const [metricsStatus, setMetricsStatus] = useState<string>('ok');

  // Define functions before use
  const loadProductInfo = async () => {
    const resp = await listProducts();
    const p = resp.items.find(i => i.id === productId);
    if (p) setProduct(p);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Metrics
      const mResp = await getProductMetrics(productId, window);
      setMetrics(mResp.metrics);
      setMetricsStatus(mResp.status);

      // 2. Valuations (for chart)
      let start = dayjs();
      if (window === '4w') start = start.subtract(4, 'week');
      else if (window === '8w') start = start.subtract(8, 'week');
      else if (window === '12w') start = start.subtract(12, 'week');
      else if (window === '24w') start = start.subtract(24, 'week');
      else if (window === '1y') start = start.subtract(1, 'year');
      else if (window === 'ytd') start = dayjs().startOf('year');
      
      const vResp = await getProductValuations(
          productId, 
          start.format('YYYY-MM-DD'), 
          dayjs().format('YYYY-MM-DD')
      );
      setValuations(vResp.points);
      
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProductInfo();
  }, [productId]);

  useEffect(() => {
    if (productId) {
      loadData();
    }
  }, [productId, window]);

  const config = {
    data: valuations,
    xField: 'date',
    yField: 'market_value',
    point: {
      size: 2,
      shape: 'circle',
    },
    tooltip: {
        formatter: (datum: any) => {
            return { name: '市值', value: Number(datum.market_value).toFixed(4) };
        },
    },
    xAxis: {
        tickCount: 5,
    }
  };

  return (
    <PageContainer
      header={{
        title: product?.name || '产品详情',
        subTitle: product?.product_code,
        extra: [
            <Button key="back" onClick={() => history.back()}>
                返回
            </Button>,
            <Radio.Group key="window" value={window} onChange={e => setWindow(e.target.value)} buttonStyle="solid">
                <Radio.Button value="4w">近1月</Radio.Button>
                <Radio.Button value="8w">近2月</Radio.Button>
                <Radio.Button value="12w">近3月</Radio.Button>
                <Radio.Button value="24w">近半年</Radio.Button>
                <Radio.Button value="1y">近1年</Radio.Button>
            </Radio.Group>
        ]
      }}
    >
      <ProCard direction="column" ghost gutter={[0, 16]}>
        
        {/* 基本信息 */}
        <ProCard title="基本信息" bordered>
            <Descriptions column={3}>
                <Descriptions.Item label="机构">{product?.institution_id}</Descriptions.Item>
                <Descriptions.Item label="类型"><Tag>{product?.product_type}</Tag></Descriptions.Item>
                <Descriptions.Item label="风险等级">{product?.risk_level}</Descriptions.Item>
                <Descriptions.Item label="流动性">{product?.liquidity_rule}</Descriptions.Item>
                <Descriptions.Item label="期限">{product?.term_days}天</Descriptions.Item>
                <Descriptions.Item label="赎回到账">T+{product?.settle_days}</Descriptions.Item>
            </Descriptions>
        </ProCard>

        {/* 指标卡片 */}
        <ProCard bordered loading={loading}>
            {metricsStatus === 'insufficient_data' ? (
                <Alert message="数据不足（少于 2 周），暂不支持对比" type="warning" showIcon />
            ) : (
                <StatisticCard.Group>
                    <StatisticCard 
                        statistic={{ 
                            title: '年化收益率', 
                            value: metrics?.annualized ? (metrics.annualized * 100).toFixed(2) : '--',
                            suffix: '%',
                            precision: 2
                        }} 
                    />
                    <StatisticCard 
                        statistic={{ 
                            title: '最大回撤', 
                            value: metrics?.max_drawdown ? (metrics.max_drawdown * 100).toFixed(2) : '--',
                            suffix: '%',
                            precision: 2,
                            valueStyle: { color: 'green' }
                        }} 
                    />
                    <StatisticCard 
                        statistic={{ 
                            title: 'TWR (区间累计)', 
                            value: metrics?.twr ? (metrics.twr * 100).toFixed(2) : '--',
                            suffix: '%',
                            precision: 2
                        }} 
                    />
                    <StatisticCard 
                        statistic={{ 
                            title: '回撤修复天数', 
                            value: metrics?.drawdown_recovery_days ?? '--',
                            suffix: '天'
                        }} 
                    />
                </StatisticCard.Group>
            )}
        </ProCard>

        {/* 估值曲线 */}
        <ProCard title="估值走势" bordered loading={loading}>
            {valuations.length > 0 ? (
                <Line {...config} />
            ) : (
                <Empty description="暂无估值数据" />
            )}
        </ProCard>
      
      </ProCard>
    </PageContainer>
  );
};

export default ProductDetail;
