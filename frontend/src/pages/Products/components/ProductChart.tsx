import React from 'react';
import { Line } from '@ant-design/plots';
import { Empty, Space, Tag } from 'antd';
import dayjs from 'dayjs';
import type { ChartDataPoint, EventPoint } from '../hooks/useProductDetail';

interface ProductChartProps {
  chartData: ChartDataPoint[];
  events: EventPoint[];
  xMin?: number;
  xMax?: number;
  yMin: number;
  yMax: number;
}

const ProductChart: React.FC<ProductChartProps> = ({
  chartData,
  events,
  xMin,
  xMax,
  yMin,
  yMax,
}) => {
  const chartConfig = {
    data: chartData,
    xField: 'date',
    yField: 'value',
    shapeField: 'smooth',

    style: {
      stroke: '#1890ff',
    },
    axis: {
      x: {
        labelFormatter: (v: any) => dayjs(Number(v)).format('MM-DD'),
        labelAutoHide: true,
        min: xMin,
        max: xMax,
      },
      y: {
        labelFormatter: (v: any) => (v / 10000).toFixed(2) + '万',
        min: yMin,
        max: yMax,
      },
    },

    scale: {
      y: {
        domain: [yMin, yMax],
      },
    },

    point: {
      shapeField: 'source',
      sizeField: 'source',
      colorField: 'source',

      style: (d: any) => ({
        fill: d.source === 'manual' ? 'transparent' : undefined,
        lineDash: d.source === 'extrapolated' ? [2, 2] : undefined,
        lineWidth: 2,
      }),
      scale: {
        shape: {
          domain: ['manual', 'interpolated', 'extrapolated'],
          range: ['plus', 'point', 'point'],
        },
        size: {
          domain: ['manual', 'interpolated', 'extrapolated'],
          range: [10, 4, 4],
        },
        color: {
          domain: ['manual', 'interpolated', 'extrapolated'],
          range: ['#ff4d4f', '#1890ff', '#999999'],
        },
      },
    },

    annotations: events.map((event) => ({
      type: 'line',
      data: [
        { x: event.date, y: 0 },
        { x: event.date, y: event.amount },
      ],
      encode: { x: 'x', y: 'y' },
      style: {
        stroke: event.type === 'buy' ? '#52c41a' : '#fa8c16',
        lineWidth: 2,
        lineDash: [4, 2],
      },
      tooltip: {
        title: '交易详情',
        items: [
          { name: '交易类型', valueFormatter: () => (event.type === 'buy' ? '买入' : '赎回') },
          { name: '交易日期', valueFormatter: () => dayjs(event.date).format('YYYY-MM-DD') },
          { name: '交易金额', valueFormatter: () => `¥${(event.amount / 10000).toFixed(2)}万` },
        ],
      },
    })),

    tooltip: {
      title: {
        channel: 'x',
        valueFormatter: (v: any) => dayjs(Number(v)).format('YYYY-MM-DD'),
      },
      items: [
        {
          name: '产品市值',
          channel: 'y',
          valueFormatter: (v: any) => (Number(v) / 10000).toFixed(4) + '万',
        },
        {
          name: '估值类型',
          field: 'source',
          valueFormatter: (v: any) => {
            if (v === 'manual') return '准确值';
            if (v === 'interpolated') return '插值估算';
            if (v === 'extrapolated') return '外推估算（仅供参考）';
            return String(v);
          },
        },
      ],
    },

    legend: {
      color: {
        itemLabel: {
          formatter: (v: string) => {
            if (v === 'manual') return '准确值';
            if (v === 'interpolated') return '插值估算';
            if (v === 'extrapolated') return '外推估算';
            return String(v);
          },
        },
        itemMarker: {
          symbol: (d: any) => (d?.value === 'manual' ? 'plus' : 'point'),
        },
      },
    },
  };

  return (
    <>
      <div style={{ height: 350 }}>
        {chartData.length > 0 ? (
          <Line {...chartConfig} />
        ) : (
          <Empty description="暂无估值数据" />
        )}
      </div>
      <Space style={{ marginTop: 8 }}>
        <Tag color="red">+ 实际估值</Tag>
        <Tag color="blue">○ 插值估算</Tag>
        <Tag color="default">◐ 外推估算</Tag>
        {events.length > 0 && (
          <>
            <Tag color="green">| 买入</Tag>
            <Tag color="orange">| 赎回</Tag>
          </>
        )}
      </Space>
    </>
  );
};

export default ProductChart;
