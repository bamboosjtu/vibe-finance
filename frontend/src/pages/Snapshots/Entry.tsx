import React, { useState, useEffect } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { EditableProTable } from '@ant-design/pro-components';
import type { ProColumns } from '@ant-design/pro-components';
import { Button, DatePicker, message, Card, Space } from 'antd';
import dayjs from 'dayjs';
import { listAccounts, Account } from '@/services/accounts';
import { listInstitutions, Institution } from '@/services/institutions';
import { batchUpsertSnapshots, listSnapshots, SnapshotItem } from '@/services/snapshots';

type DataSourceType = {
  id: React.Key;
  account_id: number;
  account_name: string;
  institution_name: string;
  type: string;
  balance: number | null;
  latest_balance?: number | null;
  latest_date?: string | null;
};

const SnapshotEntry: React.FC = () => {
  const [date, setDate] = useState<dayjs.Dayjs>(dayjs());
  const [editableKeys, setEditableRowKeys] = useState<React.Key[]>([]);
  const [dataSource, setDataSource] = useState<DataSourceType[]>([]);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // 加载数据
  const loadData = async (targetDate: dayjs.Dayjs) => {
    setLoading(true);
    try {
      const dateStr = targetDate.format('YYYY-MM-DD');

      // 并行获取账户列表、机构列表和当天的快照
      const [accountsResp, institutionsResp, snapshotsResp] = await Promise.all([
        listAccounts(),
        listInstitutions(),
        listSnapshots(dateStr).catch(() => ({ items: [] } as any)) // 如果快照不存在，返回空
      ]);

      const accounts = accountsResp.items || [];
      const institutions = institutionsResp.items || [];
      const institutionMap = new Map(institutions.map((inst: Institution) => [inst.id, inst.name]));
      const snapshots = snapshotsResp.items || [];
      const snapshotMap = new Map(snapshots.map((s: any) => [s.account_id, s.balance]));

      // 合并数据
      const data: DataSourceType[] = accounts.map((acc: Account) => {
        const bal = snapshotMap.get(acc.id);
        return {
          id: acc.id,
          account_id: acc.id,
          account_name: acc.name,
          institution_name: institutionMap.get(acc.institution_id) || '-',
          type: acc.type,
          // 如果后端返回了该日的快照，balance 应该是一个数字
          // 如果没有，balance 是 null。
          // 确保 0 也能被正确显示
          balance: (bal !== undefined && bal !== null) ? Number(bal) : null,
          latest_balance: acc.latest_balance,
          latest_date: acc.latest_date,
        };
      });

      setDataSource(data);
      setEditableRowKeys(data.map(item => item.id)); // 默认全部可编辑
      setReloadKey(prev => prev + 1);
    } catch (error) {
      console.error(error);
      message.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(date);
  }, [date]);

  const handleSave = async () => {
    const rows: SnapshotItem[] = dataSource
      .filter(item => item.balance !== null && item.balance !== undefined) // 过滤未填写的
      .map(item => ({
        date: date.format('YYYY-MM-DD'),
        account_id: item.account_id,
        balance: Number(item.balance),
      }));

    if (rows.length === 0) {
      message.warning('No data to save');
      return;
    }

    try {
      const res = await batchUpsertSnapshots({ rows });
      message.success(`Saved successfully: Inserted ${res.inserted}, Updated ${res.updated}`);
      loadData(date);
    } catch (error: any) {
      message.error(error.message || 'Save failed');
    }
  };

  const columns: ProColumns<DataSourceType>[] = [
    {
      title: '机构',
      dataIndex: 'institution_name',
      readonly: true,
      width: '15%',
    },
    {
      title: '账户名称',
      dataIndex: 'account_name',
      readonly: true,
      width: '20%',
    },
    {
      title: '类型',
      dataIndex: 'type',
      readonly: true,
      width: '12%',
      valueEnum: {
        cash: { text: '现金', status: 'Success' },
        debit: { text: '储蓄卡', status: 'Processing' },
        credit: { text: '信用卡', status: 'Error' },
        investment_cash: { text: '投资账户', status: 'Warning' },
        other: { text: '其他', status: 'Default' },
      },
    },
    {
      title: '最近更新日',
      dataIndex: 'latest_date',
      readonly: true,
      width: '15%',
      valueType: 'date',
      render: (_, record: any) => {
        return record.latest_date ? record.latest_date : '-';
      }
    },
    {
      title: '最新余额',
      dataIndex: 'latest_balance',
      readonly: true,
      width: '20%',
      valueType: 'money',
      render: (_, record: any) => {
        // We need to pass latest_balance from API first
        return record.latest_balance !== undefined && record.latest_balance !== null 
          ? record.latest_balance 
          : '-';
      }
    },
    {
      title: '余额',
      dataIndex: 'balance',
      valueType: 'money',
      width: '30%',
      fieldProps: {
        autoFocus: false,
        placeholder: '未录入',
      }
    },
  ];

  return (
    <PageContainer title="资产快照录入">
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <span>选择日期：</span>
          <DatePicker 
            value={date} 
            onChange={(d) => d && setDate(d)} 
            allowClear={false}
          />
          <Button type="primary" onClick={handleSave} loading={loading}>
            保存当前快照
          </Button>
          <Button onClick={() => loadData(date)}>
            刷新
          </Button>
        </Space>
        
        <EditableProTable<DataSourceType>
          key={reloadKey}
          rowKey="id"
          headerTitle={`资产清单 (${date.format('YYYY-MM-DD')})`}
          loading={loading}
          columns={columns}
          value={dataSource}
          onChange={(val) => setDataSource([...val])}
          recordCreatorProps={false}
          editable={{
            type: 'multiple',
            editableKeys,
            onChange: setEditableRowKeys,
            onValuesChange: (record, recordList) => {
              setDataSource([...recordList]);
            },
          }}
        />
      </Card>
    </PageContainer>
  );
};

export default SnapshotEntry;
