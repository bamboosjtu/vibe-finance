import { useState, useEffect, useCallback } from 'react';
import { getProductMetrics, listProducts, Product, ProductMetrics, getProductChart } from '@/services/products';
import { getProductTransactions, Transaction } from '@/services/transactions';
import { listAccounts, Account } from '@/services/accounts';

export type WindowType = '4w' | '8w' | '12w' | '24w' | '1y' | 'ytd';

export interface ChartDataPoint {
  date: number;
  value: number;
  source: 'manual' | 'interpolated' | 'extrapolated';
}

export interface EventPoint {
  date: number;
  type: 'buy' | 'redeem';
  amount: number;
}

export interface ValuationRow {
  id: string;
  date: string;
  market_value: number;
}

export interface UseProductDetailReturn {
  // 基础数据
  product: Product | null;
  accounts: Account[];
  
  // 窗口和指标
  window: WindowType;
  setWindow: (window: WindowType) => void;
  metrics: ProductMetrics | null;
  metricsStatus: 'ok' | 'insufficient_data' | 'degraded';
  metricsDegradedReason: string | undefined;
  
  // 图表数据
  chartData: ChartDataPoint[];
  events: EventPoint[];
  xMin: number | undefined;
  xMax: number | undefined;
  yMin: number;
  yMax: number;
  
  // 交易记录
  transactions: Transaction[];
  
  // 估值表格数据
  valuationDataSource: ValuationRow[];
  
  // 加载状态
  loading: boolean;
  
  // 刷新数据
  refresh: () => Promise<void>;
}

export function useProductDetail(productId: number): UseProductDetailReturn {
  // 产品信息
  const [product, setProduct] = useState<Product | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  
  // 窗口和指标
  const [window, setWindow] = useState<WindowType>('8w');
  const [metrics, setMetrics] = useState<ProductMetrics | null>(null);
  const [metricsStatus, setMetricsStatus] = useState<'ok' | 'insufficient_data' | 'degraded'>('ok');
  const [metricsDegradedReason, setMetricsDegradedReason] = useState<string | undefined>(undefined);
  
  // 走势数据
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [events, setEvents] = useState<EventPoint[]>([]);
  
  // Y轴范围
  const [yMin, setYMin] = useState<number>(0);
  const [yMax, setYMax] = useState<number>(100000);
  const [xMin, setXMin] = useState<number | undefined>();
  const [xMax, setXMax] = useState<number | undefined>();
  
  // 交易记录
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  
  // 估值录入表格
  const [valuationDataSource, setValuationDataSource] = useState<ValuationRow[]>([]);
  
  // 加载状态
  const [loading, setLoading] = useState(false);

  // 加载产品信息（只加载一次）
  useEffect(() => {
    listProducts().then(resp => {
      const p = resp.items.find(item => item.id === productId);
      if (p) setProduct(p);
    });
    listAccounts().then(resp => setAccounts(resp.items));
  }, [productId]);

  // 加载走势和指标数据
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 加载指标
      const mResp = await getProductMetrics(productId, window);
      setMetrics(mResp.metrics);
      setMetricsStatus(mResp.status);
      setMetricsDegradedReason(mResp.degraded_reason);

      // 加载走势数据
      const vResp = await getProductChart(productId, window);
      const points = vResp.points.map(p => ({
        date: new Date(p.date).getTime(),
        value: p.market_value,
        source: p.source,
      }));
      setChartData(points);

      // 加载交易记录（与市值走势使用相同的window参数）
      const tResp = await getProductTransactions(productId, { window });
      setTransactions(tResp.items);

      // 转换交易为事件点
      const eventPoints: EventPoint[] = tResp.items.map(t => ({
        date: new Date(t.trade_date).getTime(),
        type: t.category === 'buy' ? 'buy' : 'redeem',
        amount: t.amount,
      }));
      setEvents(eventPoints);

      // 计算 Y 轴范围
      // Sprint 3-3 要求: Y轴基于市值序列，并考虑买入/卖出当日的市值跳变
      const marketValueMin = points.length > 0 ? Math.min(...points.map(d => d.value)) : 0;
      const marketValueMax = points.length > 0 ? Math.max(...points.map(d => d.value)) : 100000;
      const eventAmountMax = eventPoints.length > 0 ? Math.max(...eventPoints.map(e => Math.abs(e.amount))) : 0;
      // 考虑事件金额对Y轴范围的影响，确保大额交易不会压扁历史走势
      const calculatedYMin = Math.min(marketValueMin * 0.9999, marketValueMin - eventAmountMax * 0.0001);
      const calculatedYMax = Math.max(marketValueMax * 1.0001, marketValueMax + eventAmountMax * 0.0001);
      setXMin(points.length > 0 ? Math.min(...points.map(d => d.date)) : 0);
      setYMin(calculatedYMin);
      setXMax(points.length > 0 ? Math.max(...points.map(d => d.date)) : 0);
      setYMax(calculatedYMax);

      // 准备估值录入表格数据（只显示manual点）
      const manualPoints = vResp.points.filter(p => p.source === 'manual');
      setValuationDataSource(manualPoints.map(p => ({
        id: p.date,
        date: p.date,
        market_value: p.market_value,
      })));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [productId, window]);

  // 窗口变化时重新加载数据
  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
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
    loading,
    refresh: loadData,
  };
}
