# DataPilot Frontend

DataPilot 前端应用，基于 Vue 3、TypeScript 和 Vite 构建，为本地电商数据分析与异常检测 Agent 提供 Web 操作界面。

## 技术栈

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Element Plus
- Axios

## 功能页面

| 页面 | 路由 | 功能 |
|---|---|---|
| 经营概览 | `/` | 查看经营数据概况 |
| Agent 对话 | `/agent` | 与数据分析 Agent 交互 |
| 数据管理 | `/data-management` | 导入和管理业务数据、查看数据质量 |
| 业务分析 | `/analytics` | 查看业务趋势和品类分析 |
| 异常检测 | `/anomalies` | 查看业务异常检测结果 |

## 环境要求

- Node.js 24+
- npm 12+

## 本地开发

在项目根目录启动后端服务，并确保后端 API 监听 `127.0.0.1:8011`。

然后进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

开发服务器会将 `/api` 请求代理到：

```text
http://127.0.0.1:8011
```

代理配置位于 `vite.config.ts`。

## 生产构建

```bash
npm run build
```

构建前会执行 TypeScript 项目检查，成功后由 Vite 生成生产文件，默认输出到 `dist/`。

本地预览生产构建：

```bash
npm run preview
```

## 项目结构

```text
frontend/
├── src/
│   ├── api/          # 后端 API 请求
│   ├── assets/       # 静态资源
│   ├── components/   # 通用组件
│   ├── layouts/      # 页面布局
│   ├── router/       # 路由配置
│   ├── stores/       # Pinia 状态管理
│   ├── views/        # 业务页面
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── vite.config.ts
└── README.md
```

## 相关说明

- 前端通过后端 REST API 获取业务数据。
- 本地开发使用 Vite 代理转发 `/api` 请求。
- 生产环境由 Nginx 托管静态资源并代理后端 API，具体配置见项目根目录的 Docker 部署配置。
