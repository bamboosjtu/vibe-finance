// 运行时配置
import { history } from '@umijs/max';
import { message } from 'antd';
import { AccountBookOutlined, BarChartOutlined, DashboardOutlined } from '@ant-design/icons';
import React from 'react';

// 全局初始化数据配置，用于 Layout 用户信息和权限初始化
export async function getInitialState(): Promise<{ name: string }> {
  return { name: '投资记录分析工具' };
}

export const layout = () => {
  return {
    title: '投资记录分析工具',
    menu: {
      locale: false,
    },
    navTheme: 'light',
    colorPrimary: '#1890ff',
    layout: 'side',
    contentWidth: 'Fluid',
    fixedHeader: true,
    fixSiderbar: true,
    colorWeak: false,
    menuHeaderRender: undefined,
    rightContentRender: () => null,
    actionsRender: () => [],
    avatarProps: {
      render: () => null,
    },
    // 自定义菜单
    menuDataRender: () => [
      {
        path: '/dashboard',
        name: 'Dashboard',
        icon: React.createElement(DashboardOutlined),
      },
      {
        path: '/accounts',
        name: '账户',
        icon: React.createElement(AccountBookOutlined),
      },
      {
        path: '/products',
        name: '产品',
        icon: React.createElement(BarChartOutlined),
      },
    ],
  };
};
