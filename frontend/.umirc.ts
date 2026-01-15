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
    title: '@umijs/max',
  },
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      name: 'Dashboard',
      path: '/dashboard',
      component: './Home',
    },
    {
      name: '首页',
      path: '/home',
      component: './Home',
    },
    {
      name: '账户',
      path: '/accounts',
      component: './Accounts',
    },
    {
      name: '产品',
      path: '/products',
      component: './Products',
    },
  ],
  npmClient: 'npm',
});

