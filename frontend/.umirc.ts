import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  model: {},
  initialState: {},
  request: {},
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    },
  },
  layout: {
    title: 'Vibe Investment',
    locale: false,
    layout: 'side',
  },
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      name: 'Dashboard',
      path: '/dashboard',
      component: './Dashboard',
      icon: 'dashboard',
    },
    {
      name: '录入（事实）',
      path: '/entry',
      icon: 'edit',
      routes: [
        {
          path: '/entry',
          redirect: '/entry/snapshots',
        },
        {
          name: '资产快照',
          path: '/entry/snapshots',
          component: './Snapshots/Entry',
        },
      ],
    },
    {
      name: '主数据',
      path: '/master',
      icon: 'database',
      routes: [
        {
          path: '/master',
          redirect: '/master/accounts',
        },
        {
          name: '账户',
          path: '/master/accounts',
          component: './Accounts',
        },
        {
          name: '产品',
          path: '/master/products',
          component: './Products',
        },
      ],
    },
    {
      path: '/products/:id',
      component: './Products/Detail',
      hideInMenu: true,
    },
  ],
  npmClient: 'npm',
});

