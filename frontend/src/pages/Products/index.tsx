import { Card, Button, Table, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const Products: React.FC = () => {
  const columns = [
    {
      title: '产品名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '机构',
      dataIndex: 'institution',
      key: 'institution',
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => <Tag color="blue">{level}</Tag>,
    },
    {
      title: '期限',
      dataIndex: 'term_days',
      key: 'term_days',
      render: (days: number) => days ? `${days}天` : '无期限',
    },
    {
      title: '流动性规则',
      dataIndex: 'liquidity_rule',
      key: 'liquidity_rule',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1>产品管理</h1>
        <Button type="primary" icon={<PlusOutlined />}>
          新建产品
        </Button>
      </div>
      
      <Card title="产品列表 - Sprint 0 占位页">
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

export default Products;
