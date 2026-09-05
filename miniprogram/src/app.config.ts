export default defineAppConfig({
  pages: [
    'pages/home/index',
    'pages/convert/index',
    'pages/preview/index',
    'pages/editor/index',
    'pages/works/index',
    'pages/make/index',
    'pages/settings/index',
    'pages/privacy/index',
  ],
  window: {
    navigationBarBackgroundColor: '#fffaf3',
    navigationBarTextStyle: 'black',
    navigationBarTitleText: '拼豆助手',
    backgroundColor: '#fffaf3',
    backgroundTextStyle: 'dark',
  },
  tabBar: {
    color: '#766f67',
    selectedColor: '#cc5f43',
    backgroundColor: '#ffffff',
    borderStyle: 'white',
    list: [
      { pagePath: 'pages/home/index', text: '首页' },
      { pagePath: 'pages/works/index', text: '作品' },
      { pagePath: 'pages/settings/index', text: '设置' },
    ],
  },
  lazyCodeLoading: 'requiredComponents',
})
