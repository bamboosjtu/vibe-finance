// 运行时配置

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
  };
};
