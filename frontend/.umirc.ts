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
      name: '账户',
      path: '/accounts',
      icon: 'accountBook',
      routes: [
        {
          path: '/accounts',
          redirect: '/accounts/list',
        },
        {
          name: '账户列表',
          path: '/accounts/list',
          component: './Accounts',
        },
        {
          name: '资产快照',
          path: '/accounts/snapshots',
          component: './Snapshots/Entry',
        },
      ],
    },
    {
      name: '产品',
      path: '/products',
      icon: 'barChart',
      routes: [
        {
          path: '/products',
          redirect: '/products/list',
        },
        {
          name: '产品列表',
          path: '/products/list',
          component: './Products',
        },
        {
          name: '产品估值',
          path: '/products/valuations',
          component: './ProductValuations',
        },
      ],
    },
    {
      path: '/products/:id',
      component: './Products/Detail',
    },
  ],
  npmClient: 'npm',
});

