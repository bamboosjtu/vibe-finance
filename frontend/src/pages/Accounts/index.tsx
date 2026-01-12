import { Card, Button, Table } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const Accounts: React.FC = () => {
  const columns = [
    {
      title: '账户名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '机构',
      dataIndex: 'institution',
      key: 'institution',
    },
    {
      title: '计入可用现金',
      dataIndex: 'is_liquid',
      key: 'is_liquid',
      render: (isLiquid: boolean) => (isLiquid ? '✓' : '×'),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1>账户管理</h1>
        <Button type="primary" icon={<PlusOutlined />}>
          新建账户
        </Button>
      </div>
      
      <Card title="账户列表 - Sprint 0 占位页">
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Accounts;
