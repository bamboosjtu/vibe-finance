import { Card, Row, Col, Statistic } from 'antd';
import { AccountBookOutlined, BankOutlined, CreditCardOutlined, DollarOutlined } from '@ant-design/icons';

const Dashboard: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h1>Dashboard</h1>
      <p>投资概览页面 - Sprint 0 占位页</p>
      
      <Row gutter={16} style={{ marginTop: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总资产"
              value={0}
              prefix={<BankOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="流动资产"
              value={0}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="负债"
              value={0}
              prefix={<CreditCardOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="可用现金"
              value={0}
              prefix={<AccountBookOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
