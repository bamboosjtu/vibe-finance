import { PlusOutlined } from '@ant-design/icons';
import {
  ActionType,
  ModalForm,
  PageContainer,
  ProFormDigit,
  ProFormSelect,
  ProFormText,
  ProFormTextArea,
  ProTable,
} from '@ant-design/pro-components';
import { Button, Form, message, Popconfirm, Tag } from 'antd';
import React, { useMemo, useRef, useState } from 'react';

import type { Institution } from '@/services/institutions';
import { createInstitution, listInstitutions } from '@/services/institutions';
import type {
  CreateProductReq,
  LiquidityRule,
  PatchProductReq,
  Product,
  ProductType,
  ProductWithMetrics,
} from '@/services/products';
import { createProduct, listProducts, patchProduct, deleteProduct } from '@/services/products';
import { history } from '@umijs/max';

import styles from './index.less';

type ProductFormValues = {
  name: string;
  institution_id?: number | null;
  product_code?: string | null;
  product_type: ProductType;
  risk_level?: string | null;
  term_days?: number | null;
  liquidity_rule: LiquidityRule;
  settle_days?: number;
  note?: string | null;
};

type InstitutionFormValues = {
  name: string;
};

const Products: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [institutionCreateOpen, setInstitutionCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Product | undefined>(undefined);
  const [productForm] = Form.useForm<ProductFormValues>();
  const [institutionForm] = Form.useForm<InstitutionFormValues>();

  const institutionNameById = useMemo(() => {
    const map = new Map<number, string>();
    institutions.forEach((i) => map.set(i.id, i.name));
    return map;
  }, [institutions]);

  const loadInstitutions = async () => {
    try {
      const resp = await listInstitutions();
      setInstitutions(resp.items);
    } catch (e) {
      message.error('加载机构列表失败');
      setInstitutions([]);
    }
  };

  const productTypeEnum: Record<ProductType, { text: string }> = {
    bank_wmp: { text: '银行理财' },
    money_market: { text: '货币/活期类' },
    term_deposit: { text: '定期存款' },
    fund: { text: '基金' },
    stock: { text: '股票' },
    other: { text: '其他' },
  };

  const liquidityRuleEnum: Record<LiquidityRule, { text: string }> = {
    open: { text: '开放' },
    closed: { text: '封闭' },
    periodic_open: { text: '定开' },
  };

  return (
    <PageContainer
      header={{
        title: '产品',
      }}
      extra={[
        <Button
          key="create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={async () => {
            await loadInstitutions();
            productForm.resetFields();
            setCreateOpen(true);
          }}
        >
          新建产品
        </Button>,
      ]}
    >
      <div className={styles.toolbar} />
      <ProTable<ProductWithMetrics>
        actionRef={actionRef}
        rowKey="id"
        search={false}
        request={async () => {
          await loadInstitutions();
          const resp = await listProducts(true);
          return {
            data: resp.items,
            success: true,
          };
        }}
        columns={[
          {
            title: '产品名',
            dataIndex: 'name',
            render: (dom, record) => <a onClick={() => history.push(`/products/${record.id}`)}>{dom}</a>,
          },
          {
            title: '机构',
            dataIndex: 'institution_id',
            render: (_, record) => {
              if (!record.institution_id) return '-';
              return institutionNameById.get(record.institution_id) || String(record.institution_id);
            },
          },
          {
            title: '风险等级',
            dataIndex: 'risk_level',
            render: (_, record) => {
              if (!record.risk_level) return '-';
              return <Tag color="blue">{record.risk_level}</Tag>;
            },
          },
          {
            title: '期限',
            dataIndex: 'term_days',
            render: (_, record) => {
              if (record.term_days === null || record.term_days === undefined) return '-';
              if (record.term_days === 0) return '0天';
              return `${record.term_days}天`;
            },
          },
          {
            title: '赎回规则',
            dataIndex: 'liquidity_rule',
            valueEnum: liquidityRuleEnum,
          },
          {
            title: '产品总金额',
            dataIndex: 'total_holding_amount',
            render: (_, record) =>
              record.total_holding_amount ? (
                `¥${record.total_holding_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              ) : (
                <span style={{ color: '#ccc' }}>¥0.00</span>
              ),
          },
          {
            title: '参考收益率',
            children: [
              {
                title: '1月',
                dataIndex: ['metrics_by_window', '4w', 'annualized'],
                width: 70,
                render: (_, record) => {
                  const val = record.metrics_by_window?.['4w']?.annualized;
                  return val !== undefined ? `${val.toFixed(2)}%` : <span style={{ color: '#ccc' }}>--</span>;
                },
              },
              {
                title: '2月',
                dataIndex: ['metrics_by_window', '8w', 'annualized'],
                width: 70,
                render: (_, record) => {
                  const val = record.metrics_by_window?.['8w']?.annualized;
                  return val !== undefined ? `${val.toFixed(2)}%` : <span style={{ color: '#ccc' }}>--</span>;
                },
              },
              {
                title: '3月',
                dataIndex: ['metrics_by_window', '12w', 'annualized'],
                width: 70,
                render: (_, record) => {
                  const val = record.metrics_by_window?.['12w']?.annualized;
                  return val !== undefined ? `${val.toFixed(2)}%` : <span style={{ color: '#ccc' }}>--</span>;
                },
              },
              {
                title: '半年',
                dataIndex: ['metrics_by_window', '24w', 'annualized'],
                width: 70,
                render: (_, record) => {
                  const val = record.metrics_by_window?.['24w']?.annualized;
                  return val !== undefined ? `${val.toFixed(2)}%` : <span style={{ color: '#ccc' }}>--</span>;
                },
              },
              {
                title: '1年',
                dataIndex: ['metrics_by_window', '1y', 'annualized'],
                width: 70,
                render: (_, record) => {
                  const val = record.metrics_by_window?.['1y']?.annualized;
                  return val !== undefined ? `${val.toFixed(2)}%` : <span style={{ color: '#ccc' }}>--</span>;
                },
              },
            ],
          },
          {
            title: '最大回撤',
            dataIndex: ['metrics', 'max_drawdown'],
            sorter: (a, b) => (a.metrics?.max_drawdown || 999) - (b.metrics?.max_drawdown || 999),
            render: (_, record) =>
              record.metrics ? (
                `${record.metrics.max_drawdown.toFixed(2)}%`
              ) : (
                <span style={{ color: '#ccc' }}>--</span>
              ),
          },
          {
            title: '修复天数',
            dataIndex: ['metrics', 'drawdown_recovery_days'],
            render: (_, record) =>
              record.metrics ? (
                `${record.metrics.drawdown_recovery_days}天`
              ) : (
                <span style={{ color: '#ccc' }}>--</span>
              ),
          },
          {
            title: '操作',
            valueType: 'option',
            render: (_, record) => [
              <a key="detail" onClick={() => history.push(`/products/${record.id}`)}>
                详情
              </a>,
              <a
                key="edit"
                onClick={async () => {
                  await loadInstitutions();
                  setEditing(record);
                  productForm.setFieldsValue({
                    name: record.name,
                    institution_id: record.institution_id,
                    product_code: record.product_code,
                    product_type: record.product_type,
                    risk_level: record.risk_level,
                    term_days: record.term_days,
                    liquidity_rule: record.liquidity_rule,
                    settle_days: record.settle_days,
                    note: record.note,
                  });
                  setEditOpen(true);
                }}
              >
                编辑
              </a>,
              <Popconfirm
                key="delete"
                title="确定删除此产品吗？"
                description="删除后，相关的估值数据也将被删除，且不可恢复。"
                onConfirm={async () => {
                  try {
                    await deleteProduct(record.id);
                    message.success('删除成功');
                    actionRef.current?.reload();
                  } catch (e) {
                    console.error('Delete failed:', e);
                    message.error('删除失败');
                  }
                }}
              >
                <a style={{ color: 'red', marginLeft: 8 }}>删除</a>
              </Popconfirm>,
            ],
          },
        ]}
      />

      <ModalForm<ProductFormValues>
        form={productForm}
        title="新建产品"
        open={createOpen}
        onOpenChange={(v) => setCreateOpen(v)}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          try {
            const payload: CreateProductReq = {
              name: values.name,
              institution_id: values.institution_id ?? null,
              product_code: values.product_code ?? null,
              product_type: values.product_type,
              risk_level: values.risk_level ?? null,
              term_days: values.term_days ?? null,
              liquidity_rule: values.liquidity_rule,
              settle_days: values.settle_days,
              note: values.note ?? null,
            };
            await createProduct(payload);
            message.success('创建成功');
            actionRef.current?.reload();
            return true;
          } catch (e) {
            message.error('创建失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="产品名" rules={[{ required: true }]} />
        <ProFormSelect
          name="institution_id"
          label="机构"
          options={institutions.map((i) => ({ label: i.name, value: i.id }))}
          fieldProps={{
            allowClear: true,
            dropdownRender: (menu) => (
              <div>
                {menu}
                <div>
                  <Button
                    type="link"
                    onClick={() => {
                      institutionForm.resetFields();
                      setInstitutionCreateOpen(true);
                    }}
                  >
                    新建机构
                  </Button>
                </div>
              </div>
            ),
          }}
        />
        <ProFormText name="product_code" label="产品代码" />
        <ProFormSelect
          name="product_type"
          label="产品类型"
          valueEnum={productTypeEnum}
          rules={[{ required: true }]}
        />
        <ProFormSelect
          name="risk_level"
          label="风险等级"
          allowClear
          options={['R1', 'R2', 'R3', 'R4', 'R5'].map((r) => ({ label: r, value: r }))}
        />
        <ProFormDigit name="term_days" label="期限天数" fieldProps={{ precision: 0 }} />
        <ProFormSelect
          name="liquidity_rule"
          label="流动性规则"
          valueEnum={liquidityRuleEnum}
          rules={[{ required: true }]}
          fieldProps={{
            onChange: (v) => {
              if (v === 'open') {
                const current = productForm.getFieldValue('term_days');
                if (current === undefined) {
                  productForm.setFieldsValue({ term_days: 0 });
                }
              }
            },
          }}
        />
        <ProFormDigit name="settle_days" label="赎回到账 T+N" fieldProps={{ precision: 0 }} />
        <ProFormTextArea name="note" label="备注" />
      </ModalForm>

      <ModalForm<ProductFormValues>
        form={productForm}
        title="编辑产品"
        open={editOpen}
        onOpenChange={(v) => {
          setEditOpen(v);
          if (!v) setEditing(undefined);
        }}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          if (!editing) return false;
          try {
            const payload: PatchProductReq = {
              name: values.name,
              institution_id: values.institution_id ?? null,
              product_code: values.product_code ?? null,
              product_type: values.product_type,
              risk_level: values.risk_level || null,
              term_days: values.term_days ?? null,
              liquidity_rule: values.liquidity_rule,
              settle_days: values.settle_days,
              note: values.note ?? null,
            };
            await patchProduct(editing.id, payload);
            message.success('保存成功');
            actionRef.current?.reload();
            return true;
          } catch (e) {
            message.error('保存失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="产品名" rules={[{ required: true }]} />
        <ProFormSelect
          name="institution_id"
          label="机构"
          options={institutions.map((i) => ({ label: i.name, value: i.id }))}
          fieldProps={{ allowClear: true }}
        />
        <ProFormText name="product_code" label="产品代码" />
        <ProFormSelect
          name="product_type"
          label="产品类型"
          valueEnum={productTypeEnum}
          rules={[{ required: true }]}
        />
        <ProFormSelect
          name="risk_level"
          label="风险等级"
          allowClear
          options={['R1', 'R2', 'R3', 'R4', 'R5'].map((r) => ({ label: r, value: r }))}
        />
        <ProFormDigit name="term_days" label="期限天数" fieldProps={{ precision: 0 }} />
        <ProFormSelect
          name="liquidity_rule"
          label="流动性规则"
          valueEnum={liquidityRuleEnum}
          rules={[{ required: true }]}
        />
        <ProFormDigit name="settle_days" label="赎回到账 T+N" fieldProps={{ precision: 0 }} />
        <ProFormTextArea name="note" label="备注" />
      </ModalForm>

      <ModalForm<InstitutionFormValues>
        form={institutionForm}
        title="新建机构"
        open={institutionCreateOpen}
        onOpenChange={(v) => setInstitutionCreateOpen(v)}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          try {
            const created = await createInstitution({ name: values.name });
            message.success('创建成功');
            await loadInstitutions();
            productForm.setFieldsValue({ institution_id: created.id });
            return true;
          } catch (e) {
            message.error('创建失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="机构名称" rules={[{ required: true }]} />
      </ModalForm>
    </PageContainer>
  );
};

export default Products;
