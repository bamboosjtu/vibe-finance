import React, { useState, useEffect } from 'react';
import { PageContainer, EditableProTable, ProColumns } from '@ant-design/pro-components';
import { message, Select, Popconfirm } from 'antd';
import dayjs from 'dayjs';
import { listProducts, Product } from '@/services/products';
import { batchUpsertValuations, getProductValuations, ProductValuation, deleteProductValuation } from '@/services/valuations';

// Define the type used in the table which includes the synthetic 'id'
type TableItem = ProductValuation & { id: string };

const ProductValuations: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [editableKeys, setEditableRowKeys] = useState<React.Key[]>([]);
  const [dataSource, setDataSource] = useState<TableItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Define functions before use
  const loadProducts = async () => {
    try {
      const resp = await listProducts();
      setProducts(resp.items);
      // 默认选择"国债逆回购"
      const defaultProduct = resp.items.find(p => p.name === '国债逆回购');
      if (defaultProduct) {
        setSelectedProductId(defaultProduct.id);
      }
    } catch (e) {
      message.error('加载产品列表失败');
    }
  };

  const loadValuations = async (productId: number) => {
    setLoading(true);
    try {
      const end = dayjs().format('YYYY-MM-DD');
      const start = dayjs().subtract(1, 'year').format('YYYY-MM-DD');
      const resp = await getProductValuations(productId, start, end);
      const data = resp.points.map((p) => ({
        ...p,
        id: `${p.date}`,
      }));
      data.sort((a, b) => dayjs(b.date).valueOf() - dayjs(a.date).valueOf());
      setDataSource(data);
    } catch (e) {
      message.error('加载估值数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (selectedProductId) {
      loadValuations(selectedProductId);
    } else {
      setDataSource([]);
    }
  }, [selectedProductId]);

  const columns: ProColumns<TableItem>[] = [
    {
      title: '日期',
      dataIndex: 'date',
      valueType: 'date',
      width: '40%',
      formItemProps: {
        rules: [{ required: true, message: '此项是必填项' }],
      },
    },
    {
      title: '市值/净值',
      dataIndex: 'market_value',
      valueType: 'money',
      width: '40%',
      fieldProps: {
        precision: 4,
      },
      formItemProps: {
        rules: [{ required: true, message: '此项是必填项' }],
      },
    },
    {
      title: '操作',
      valueType: 'option',
      width: '20%',
      render: (text, record, _, action) => [
        <a
          key="editable"
          onClick={() => {
            action?.startEditable?.(record.id);
          }}
        >
          编辑
        </a>,
        <Popconfirm
          key="delete"
          title="确定删除这条估值记录吗？"
          onConfirm={async () => {
             if (!selectedProductId) return;
             try {
                await deleteProductValuation(selectedProductId, record.date);
                message.success('删除成功');
                loadValuations(selectedProductId);
             } catch (e) {
                message.error('删除失败');
             }
          }}
        >
          <a style={{ color: 'red' }}>删除</a>
        </Popconfirm>,
      ],
    },
  ];

  return (
    <PageContainer
      header={{
        title: '产品估值',
        extra: [
          <Select
            key="product-select"
            style={{ width: 200 }}
            placeholder="选择产品"
            options={products.map(p => ({ label: p.name, value: p.id }))}
            value={selectedProductId}
            onChange={setSelectedProductId}
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />
        ],
      }}
    >
      <EditableProTable<TableItem>
        rowKey="id"
        headerTitle="估值记录"
        recordCreatorProps={
          selectedProductId
            ? {
                position: 'top',
                record: () => ({ id: dayjs().valueOf().toString(), date: dayjs().format('YYYY-MM-DD'), market_value: 0, product_id: selectedProductId }),
                creatorButtonText: '新增一行',
              }
            : false
        }
        loading={loading}
        columns={columns}
        value={dataSource}
        onChange={(val) => setDataSource([...val])}
        editable={{
          type: 'multiple',
          editableKeys,
          onSave: async (rowKey, data) => {
            if (!selectedProductId) return;
            try {
              await batchUpsertValuations({
                source: 'manual',
                rows: [{
                  product_id: selectedProductId,
                  date: data.date,
                  market_value: data.market_value,
                }]
              });
              message.success('保存成功');
              loadValuations(selectedProductId);
            } catch (e) {
              message.error('保存失败');
              throw e;
            }
          },
          onChange: setEditableRowKeys,
          actionRender: (row, config, dom) => [dom.save, dom.cancel],
        }}
      />
    </PageContainer>
  );
};

export default ProductValuations;
