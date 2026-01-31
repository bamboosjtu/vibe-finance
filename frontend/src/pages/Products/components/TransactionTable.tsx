import React, { useState } from 'react';
import { ProTable, type ProColumns } from '@ant-design/pro-components';
import { Button, Popconfirm, Space, message, Form } from 'antd';
import { ShoppingOutlined, MoneyCollectOutlined } from '@ant-design/icons';
import { ModalForm, ProFormDatePicker, ProFormDigit, ProFormSelect, ProFormTextArea } from '@ant-design/pro-components';
import { createTransaction, deleteTransaction } from '@/services/transactions';
import type { Transaction } from '@/services/transactions';
import type { Account } from '@/services/accounts';

interface TransactionTableProps {
  productId: number;
  accounts: Account[];
  dataSource: Transaction[];
  onRefresh: () => void;
}

const TransactionTable: React.FC<TransactionTableProps> = ({
  productId,
  accounts,
  dataSource,
  onRefresh,
}) => {
  const [buyFormVisible, setBuyFormVisible] = useState(false);
  const [redeemFormVisible, setRedeemFormVisible] = useState(false);
  const [transactionForm] = Form.useForm();

  const handleCreateTransaction = async (values: any, category: string) => {
    try {
      await createTransaction({
        product_id: productId,
        account_id: values.account_id,
        category,
        trade_date: values.trade_date,
        amount: category === 'buy' ? values.amount : -values.amount,
        settle_date: values.settle_date,
        note: values.note,
      });
      message.success('操作成功');
      onRefresh();
      return true;
    } catch (e) {
      message.error('操作失败');
      return false;
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteTransaction(id);
      message.success('删除成功');
      onRefresh();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const columns: ProColumns<Transaction>[] = [
    { title: '日期', dataIndex: 'trade_date', width: 120, key: 'trade_date' },
    {
      title: '类型',
      dataIndex: 'category',
      key: 'category',
      render: (_: any, record: Transaction) => {
        const map: Record<string, string> = {
          buy: '买入',
          redeem_request: '赎回申请',
          redeem_settle: '赎回到账',
          fee: '费用',
        };
        return map[record.category] || record.category;
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (_: any, record: Transaction) => `¥${record.amount?.toLocaleString?.() || record.amount}`,
    },
    { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Transaction) => (
        <Popconfirm
          title="确认删除？"
          onConfirm={() => handleDelete(record.id)}
        >
          <a>删除</a>
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<ShoppingOutlined />} onClick={() => setBuyFormVisible(true)}>
          买入
        </Button>
        <Button icon={<MoneyCollectOutlined />} onClick={() => setRedeemFormVisible(true)}>
          赎回
        </Button>
      </Space>

      <ProTable
        rowKey="id"
        columns={columns}
        dataSource={dataSource}
        pagination={{ pageSize: 5 }}
        search={false}
        toolBarRender={false}
        options={false}
        locale={{ emptyText: '暂无交易记录' }}
      />

      {/* 买入表单 */}
      <ModalForm
        title="买入"
        open={buyFormVisible}
        onOpenChange={setBuyFormVisible}
        form={transactionForm}
        onFinish={async (values) => {
          const success = await handleCreateTransaction(values, 'buy');
          if (success) {
            setBuyFormVisible(false);
            transactionForm.resetFields();
          }
          return success;
        }}
      >
        <ProFormDatePicker name="trade_date" label="交易日期" rules={[{ required: true }]} />
        <ProFormSelect
          name="account_id"
          label="扣款账户"
          rules={[{ required: true }]}
          options={accounts.map(a => ({ label: a.name, value: a.id }))}
        />
        <ProFormDigit name="amount" label="金额" rules={[{ required: true }]} min={0} precision={2} />
        <ProFormTextArea name="note" label="备注" />
      </ModalForm>

      {/* 赎回表单 */}
      <ModalForm
        title="赎回"
        open={redeemFormVisible}
        onOpenChange={setRedeemFormVisible}
        form={transactionForm}
        onFinish={async (values) => {
          const success = await handleCreateTransaction(values, 'redeem_request');
          if (success) {
            setRedeemFormVisible(false);
            transactionForm.resetFields();
          }
          return success;
        }}
      >
        <ProFormDatePicker name="trade_date" label="申请日期" rules={[{ required: true }]} />
        <ProFormSelect
          name="account_id"
          label="到账账户"
          rules={[{ required: true }]}
          options={accounts.map(a => ({ label: a.name, value: a.id }))}
        />
        <ProFormDigit name="amount" label="金额" rules={[{ required: true }]} min={0} precision={2} />
        <ProFormDatePicker name="settle_date" label="预计到账日期" />
        <ProFormTextArea name="note" label="备注" />
      </ModalForm>
    </>
  );
};

export default TransactionTable;
