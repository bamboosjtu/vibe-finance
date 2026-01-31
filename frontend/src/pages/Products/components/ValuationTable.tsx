import React, { useState } from 'react';
import { EditableProTable, type ProColumns } from '@ant-design/pro-components';
import { Button, Popconfirm, message } from 'antd';
import dayjs from 'dayjs';
import { batchUpsertValuations, deleteValuation } from '@/services/valuations';
import type { ValuationRow } from '../hooks/useProductDetail';

interface ValuationTableProps {
  productId: number;
  dataSource: ValuationRow[];
  onChange: (data: readonly ValuationRow[]) => void;
  onRefresh: () => void;
}

const ValuationTable: React.FC<ValuationTableProps> = ({
  productId,
  dataSource,
  onChange,
  onRefresh,
}) => {
  const [editableKeys, setEditableRowKeys] = useState<React.Key[]>([]);

  const handleSave = async (rows: readonly ValuationRow[]) => {
    try {
      await batchUpsertValuations({
        rows: rows.map(r => ({
          product_id: productId,
          date: r.date,
          market_value: r.market_value,
        })),
      });
      message.success('保存成功');
      onRefresh();
      setEditableRowKeys([]);
      return true;
    } catch (e) {
      message.error('保存失败');
      return false;
    }
  };

  const handleDelete = async (date: string) => {
    try {
      await deleteValuation(productId, date);
      message.success('删除成功');
      onRefresh();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const columns: ProColumns<ValuationRow>[] = [
    {
      title: '日期',
      dataIndex: 'date',
      valueType: 'date' as const,
      width: 140,
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      valueType: 'digit' as const,
      width: 150,
      fieldProps: { precision: 2 },
    },
    {
      title: '操作',
      valueType: 'option' as const,
      width: 100,
      render: (_: any, record: ValuationRow) => [
        <Popconfirm
          key="delete"
          title="确认删除？"
          onConfirm={() => handleDelete(record.date)}
        >
          <a>删除</a>
        </Popconfirm>,
      ],
    },
  ];

  return (
    <EditableProTable<ValuationRow>
      rowKey="id"
      columns={columns}
      value={dataSource}
      onChange={onChange}
      recordCreatorProps={{
        position: 'bottom',
        record: () => ({
          id: `new_${Date.now()}`,
          date: dayjs().format('YYYY-MM-DD'),
          market_value: 0,
        }),
      }}
      editable={{
        type: 'multiple',
        editableKeys,
        onChange: setEditableRowKeys,
        actionRender: (row, config, defaultDom) => [defaultDom.save, defaultDom.delete],
      }}
      toolBarRender={() => [
        <Button
          key="save"
          type="primary"
          onClick={() => handleSave(dataSource)}
        >
          保存
        </Button>,
      ]}
    />
  );
};

export default ValuationTable;
