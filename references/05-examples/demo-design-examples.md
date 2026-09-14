# Demo设计说明示例

## 概览

本文件提供Demo设计说明书的结构示例。仅在需要参考对话框输出边界、HTML说明书输入JSON、页面说明颗粒度或完整输出示例时读取。

## 示例：数据防泄密事件分析

### 对话框输出示例

对话框主体只输出到页面总览表，页面总览之后仅给出待确认问题、HTML文件路径和简短说明。

```markdown
# 数据防泄密事件分析需求设计与编程指导

## 1. 需求概括
本需求用于帮助安全运维人员集中查看、筛选和处置数据泄密事件。

## 2. 主要用户与场景
### 2.1 主要用户角色
| 用户角色 | 岗位职责 | 核心任务 | 在Demo中关注什么 |
| -------- | -------- | -------- | ---------------- |
| 安全运维人员 | 负责日常安全事件分析和处置跟进 | 快速定位高风险事件并完成处置 | 筛选是否高效、详情是否能支撑判断、处置是否闭环 |

### 2.2 核心场景与功能映射
| 核心场景 | 用户要完成的任务 | Demo中对应能力 |
| -------- | ---------------- | -------------- |
| 事件风险定位 | 从大量事件中找到高风险和待处置事件 | 概览统计、搜索筛选、排序、分页 |
| 事件分析判断 | 查看事件证据和影响对象 | 详情抽屉、关联对象表格、证据信息 |
| 事件处置闭环 | 填写处置意见并更新状态 | 处置弹窗、二次确认、状态更新 |

## 3. Demo页面总览

### 3.1 导航结构
数据安全
└── 数据防泄密
    └── 事件分析

### 3.2 页面总览表
| 业务模块 | 页面ID | 页面名称 | 页面类型 | 页面用途 | 入口方式 | 关键交互 | 设计来源 | 编码方式 |
| -------- | ------ | -------- | -------- | -------- | -------- | -------- | -------- | -------- |
| 事件分析 | P001 | 事件列表 | 概览表格页 | 查看事件概览并筛选定位风险事件 | 菜单进入 | 搜索、筛选、查看详情、处置、导出 | 通用设计Skill | 全新开发 |
| 事件分析 | P002 | 事件详情 | 抽屉详情页 | 查看单个事件的基础信息、风险证据和影响对象 | 点击事件名称 | 关闭、处置、查看关联对象 | 通用设计Skill | 全新开发 |
| 事件分析 | P003 | 事件处置 | 弹窗表单页 | 填写处置意见并完成处置 | 点击处置按钮 | 提交、取消、二次确认 | 通用设计Skill | 全新开发 |

### 3.3 待确认问题
| 序号 | 待确认问题 | 影响范围 | 当前默认假设 |
| ---- | ---------- | -------- | ------------ |
| 1 | 事件分析是新增三级菜单，还是放在已有数据防泄密页面下作为Tab？ | 导航结构、页面入口、Coding路由 | 默认作为三级菜单“事件分析” |
| 2 | 事件处置是否需要审批流，还是安全运维人员可直接处置？ | 用户旅程、状态流转、按钮逻辑 | 默认直接处置，无审批 |

### 3.4 HTML设计说明书
- HTML文件：`./data-leak-event-demo-design-spec.html`，输出目录按输出目录判定规则确定（存在可确定的 `.demo/design/{hash}/` 时输出其中，否则默认项目根目录；本示例按默认根目录展示）。
- 说明：逐页设计说明、页面级Demo交互与逻辑规则、页面级Coding指导、Mock数据和总结性AI Coding完整提示词已写入HTML。左侧目录按页面层级展示，点击切换后右侧展示对应页面内容。

### 3.5 Coding计划与编码开始
HTML设计说明书已生成。请先查看HTML页面内容；如果HTML中有需要调整的页面结构、字段、交互、状态或说明内容，可以直接告知修改点，我会先更新并重新生成最新HTML。HTML 说明书是需用户确认的设计产物，确认后我会自动执行代码映射并输出以下 Coding Plan，随后直接开始 Coding，不再等待额外确认。

- 导航结构：数据安全 / 数据防泄密 / 事件分析，作为新增三级菜单页面开发。
- 全新开发页面：P001-事件列表、P002-事件详情抽屉、P003-事件处置弹窗。
- 参考已有页面开发：参考当前代码环境中已有表格页、详情抽屉和处置弹窗的实现方式；无指定代码时按通用组件模式实现。
- 复用已有功能点：复用表格、筛选表单、统计卡片、抽屉、弹窗、Toast、分页、loading和Mock数据组织方式。
- 新增实现功能点：事件风险筛选、统计数字联动筛选、详情证据展示、处置提交后的状态更新。
- 开发顺序：先开发P001事件列表，再接入P002事件详情抽屉，最后开发P003事件处置弹窗。

如 HTML 说明书无需调整，我将按以上 Coding Plan 自动开始编码。
```

### HTML输入JSON示例

以下 JSON 中的 `common-design/...` 文档路径（如 `common-design/references/02-template/01-page-types.md`、`common-design/references/05-components/idux-component-map.md`）为 Common Design 的真实路径，可直接引用；而 `product-design/...` 路径**本 Skill 一律不预置**：Product Design 的目录结构随产品而异，其文档路径与章节锚点必须取自当前实际加载的 Product Design Skill，示例中出现时一律写作 `<product-design 文档路径>#<章节锚点>` 占位。输出前须核对路径与该 Skill 的真实目录一致，写错会导致 `designReferences.ref` 无法在 `readLedger` 锚点级命中而被 RULE-43 `DESIGN_REF_UNREAD` 阻断，并形成无法直达原文复核的坏链。

```json
{
  "title": "数据防泄密事件分析需求设计说明书",
  "designContext": {
    "commonDesign": {"skillId": "common-design", "read": true},
    "productDesign": {"matched": false, "skillId": "", "coverage": []},
    "readLedger": [
      {"ref": "common-design/references/02-template/01-page-types.md#page-table-overview", "status": "read"},
      {"ref": "common-design/references/05-components/idux-component-map.md#*", "status": "read"},
      {"ref": "common-design/SKILL.md#*", "status": "index-only"}
    ]
  },
  "overview": {
    "summary": "本需求用于帮助安全运维人员集中查看、筛选和处置数据泄密事件。",
    "pageOverview": [
      {"module": "事件分析", "id": "P001", "name": "事件列表", "type": "概览表格页", "purpose": "查看事件概览并筛选定位风险事件", "entry": "菜单进入", "interaction": "搜索、筛选、查看详情、处置、导出", "designSource": "通用设计Skill", "codingMode": "全新开发"},
      {"module": "事件分析", "id": "P002", "name": "事件详情", "type": "抽屉详情页", "purpose": "查看单个事件的基础信息、风险证据和影响对象", "entry": "点击事件名称", "interaction": "关闭、处置、查看关联对象", "designSource": "通用设计Skill", "codingMode": "全新开发"},
      {"module": "事件分析", "id": "P003", "name": "事件处置", "type": "弹窗表单页", "purpose": "填写处置意见并完成处置", "entry": "点击处置按钮", "interaction": "提交、取消、二次确认", "designSource": "通用设计Skill", "codingMode": "全新开发"}
    ]
  },
  "navigation": [
    {"label": "数据安全", "children": [
      {"label": "数据防泄密", "children": [
        {"label": "事件分析"}
      ]}
    ]}
  ],
  "pages": [
    {
      "id": "P001",
      "name": "事件列表",
      "type": "概览表格页",
      "navigation": {"primary": "数据安全", "secondary": "数据防泄密", "tertiary": "事件分析", "tab": ""},
      "purpose": "帮助安全运维人员快速查看数据泄密事件整体情况，并通过筛选定位需要优先处理的高风险事件。",
      "layout": "页面采用上方概览统计区 + 下方筛选表格区的结构。",
      "templateContract": {
        "templateId": "page-table-overview",
        "baseTemplateId": "",
        "templateBase": "common",
        "productTemplateRef": "",
        "navigationType": "left-shaped",
        "navigationTypeStatus": "assumed",
        "navigationTypeSource": "AI补齐",
        "navigationTypeNote": "概览表格页默认左侧菜单结构",
        "templateSource": "common-design/references/02-template/01-page-types.md#page-table-overview",
        "requiredRegions": ["global-navigation", "title-bar", "overview", "filter", "toolbar", "table", "pagination"],
        "optionalRegions": [],
        "regionOrder": ["global-navigation", "title-bar", "overview", "filter", "toolbar", "table", "pagination"],
        "footerContract": {"required": false, "alignment": "", "buttonOrder": []},
        "componentContract": {"overview": ["IxCard"], "table": ["IxTable"], "pagination": ["IxPagination"], "patternComponents": []},
        "wireframeContract": {"variantsRequired": false},
        "override": {"enabled": false, "source": "", "reason": "", "affectedRules": []}
      },
      "restoreRequirement": {"description": "还原页面骨架，骨架组件优先取匹配 Product Design 页面模板/Component 层已登记的业务封装，未登记时取 Common Design 页面模板推荐组件。", "components": [{"area": "标题栏", "iduxComponent": "页面模板指定标题栏组件", "source": "Common Design页面模板", "usage": "承载页面标题和导出、刷新等页面级操作"}, {"area": "筛选区", "iduxComponent": "IxProSearch", "source": "Common Design页面模板", "usage": "承载事件查询条件"}, {"area": "表格", "iduxComponent": "IxTable", "source": "Common Design页面模板", "usage": "承载事件列表字段和行内操作"}, {"area": "分页", "iduxComponent": "IxPagination", "source": "Common Design页面模板", "usage": "承载列表分页"}]},
      "sections": [
        {
          "title": "概览统计区",
          "description": "位于页面顶部，横向卡片排列，展示今日新增事件数、待处置事件数、高风险事件数和已处置事件数。待处置事件数和高风险事件数为可点击数字，点击后刷新下方表格并同步筛选条件。",
          "fields": ["今日新增事件数：数字，0值正常展示", "待处置事件数：可点击数字，点击筛选处置状态为待处置", "高风险事件数：可点击数字，点击筛选风险等级为高", "已处置事件数：数字"],
          "actions": ["点击高风险事件数后，列表自动筛选风险等级为高", "点击待处置事件数后，列表自动筛选处置状态为待处置"],
          "interactionNotes": ["点击统计数字后表格进入loading并刷新结果", "统计卡片不因数值为0隐藏"],
          "validationRules": ["无事件数据时所有统计展示0"]
        },
        {
          "title": "事件表格区",
          "type": "表格区",
          "description": "位于概览统计区下方，承载事件查询、导出、批量处置和单条事件操作。表格工具栏、筛选项和列表合并为一个区块描述，避免拆散同一业务对象。",
          "toolbar": ["导出按钮", "批量处置按钮", "风险等级下拉多选：高、中、低", "处置状态下拉单选：待处置、处理中、已处置", "时间范围选择器", "事件名称输入框：支持模糊搜索"],
          "filterComponent": "IxProSearch",
          "filterComponentDescription": "使用一个高级搜索组件承载风险等级、处置状态、时间范围和事件名称筛选；组件名优先取匹配 Product Design Component 层已登记的业务封装，未登记时取 Common Design 组件映射表；如果产品模板要求平铺筛选，则改为多个独立组件并逐项标注组件名称。",
          "filterFields": [{"name": "风险等级", "component": "下拉多选", "mode": "多选", "options": "高、中、低", "default": "全部", "description": "按风险等级筛选"}, {"name": "处置状态", "component": "下拉单选", "mode": "单选", "options": "待处置、处理中、已处置", "default": "全部", "description": "按处置状态筛选"}, {"name": "时间范围", "component": "日期范围选择器", "mode": "范围", "options": "最近7天、最近30天、自定义", "default": "最近7天", "description": "按发现时间范围筛选"}, {"name": "事件名称", "component": "输入框", "mode": "模糊搜索", "options": "-", "default": "空", "description": "支持模糊搜索"}],
          "tableFields": [{"name": "事件名称", "display": "可点击文本", "iduxComponent": "IxButton link", "description": "点击打开P002事件详情抽屉；长文本单行省略并悬浮展示完整内容"}, {"name": "风险等级", "display": "红/橙/蓝标签", "iduxComponent": "IxTag", "description": "状态值为高、中、低"}, {"name": "处置状态", "display": "状态点+文字", "iduxComponent": "IxBadge/IxTag", "description": "状态值为待处置、处理中、已处置"}, {"name": "发现时间", "display": "时间", "iduxComponent": "", "description": "普通文本展示，支持排序"}, {"name": "操作", "display": "操作按钮", "iduxComponent": "IxButton link", "description": "查看详情、处置"}],
          "actions": ["查询：按条件刷新表格", "重置：清空条件并恢复默认列表", "批量处置：未选择数据时提示请选择数据；已选择数据时弹出二次确认"],
          "interactionNotes": ["点击事件名称或查看详情打开P002事件详情抽屉", "点击处置打开P003处置弹窗", "导出时提示导出任务已创建", "处置成功后列表、统计卡片和详情状态同步更新"],
          "validationRules": ["搜索无结果展示暂无符合条件的数据", "查询中表格展示loading", "长事件名称单行省略并悬浮展示完整内容", "字段为空展示-", "高风险事件默认排在前面"]
        }
      ],
      "wireframe": {
        "templateId": "page-table-overview",
        "navigationType": "left-shaped",
        "layoutSource": "Common Design page-table-overview",
        "shell": {"globalNavigation": true, "titleBar": {"required": true, "type": "plain", "component": "页面模板指定标题栏组件"}, "contentContainer": {"required": true, "type": "page-content"}, "footer": {"required": false, "alignment": "", "height": "56px"}},
        "regions": [
          {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": true, "content": "全局导航"},
          {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": true, "content": "页面标题行：事件分析 [导出] [刷新]"},
          {"id": "overview", "templateRegion": "overview", "position": "content-top", "required": true, "content": "概览统计区：今日新增 | 待处置 | 高风险 | 已处置"},
          {"id": "filter", "templateRegion": "filter", "position": "content", "required": true, "content": "筛选工具栏：风险等级 处置状态 时间范围 事件名称 [查询]"},
          {"id": "table", "templateRegion": "table", "position": "content", "required": true, "content": "表格区：事件名称 | 风险等级 | 处置状态 | 发现时间 | 操作"},
          {"id": "pagination", "templateRegion": "pagination", "position": "bottom", "required": true, "content": "分页区"}
        ],
        "variants": [],
        "ascii": "┌──────────────────────────────────────────────┐\n│ 页面标题行：事件分析            [导出] [刷新] │\n├──────────────────────────────────────────────┤\n│ 概览统计区：今日新增 | 待处置 | 高风险 | 已处置 │\n├──────────────────────────────────────────────┤\n│ 筛选工具栏：风险等级 处置状态 时间范围 关键字 │\n│ 表格区：事件名称 | 风险等级 | 处置状态 | 操作 │\n│ 分页区：上一页 1 2 3 下一页                 │\n└──────────────────────────────────────────────┘"
      },
      "footerActions": ["无"],
      "codingGuide": {
        "pageContext": {
          "pageId": "P001",
          "pageType": "概览表格页",
          "route": "/data-security/event-analysis",
          "codeAvailability": "verified",
          "visualBaselineRef": "src/pages/event-analysis/index.vue"
        },
        "implementationRules": ["优先复用已验证页面和业务组件", "严格使用页面字段表中指定的组件"],
        "designReferences": [{"source": "common-design", "ref": "common-design/references/02-template/01-page-types.md#page-table-overview"}, {"source": "common-design", "ref": "common-design/references/05-components/idux-component-map.md#table"}, {"source": "ai-fill", "ref": "AI 补齐: 导航层级默认作为三级菜单"}],
        "pageItems": [
          {"id": "P001-C01", "scope": "page-shell", "name": "页面框架", "mode": "reuse-framework", "mappingRef": "M01", "mappingStatus": "verified", "target": {"path": "src/pages/event-analysis/index.vue", "export": "EventAnalysisPage"}, "dependencies": [], "requirements": ["复用XX页面整体布局和固定字段", "新增列表区和详情抽屉区"], "states": ["loading", "empty", "search-no-result"], "mockContract": {"requiredFields": ["事件名称", "风险等级", "处置状态", "发现时间"]}, "acceptanceCriteria": ["页面结构与视觉参考页面一致", "筛选、分页和行内操作可用"], "prohibitedChanges": ["不得替换已验证的表格容器"]},
          {"id": "P001-C02", "scope": "modal", "name": "处置弹窗", "mode": "component-reuse", "mappingRef": "M02", "mappingStatus": "verified", "target": {"path": "src/components/dispose-modal/index.vue", "export": "DisposeModal"}, "dependencies": ["P001-C01"], "requirements": ["复用XX页面已存在的弹窗结构和校验逻辑", "补充本页面的处置字段"], "states": ["submitting", "submit-success", "submit-failed"], "mockContract": {"updateAfterActions": ["提交处置后关闭弹窗并更新列表状态"]}, "acceptanceCriteria": ["弹窗校验规则生效", "提交后列表和统计同步更新"], "prohibitedChanges": ["不得新增真实提交接口"]},
          {"id": "P001-C03", "scope": "filter", "name": "筛选搜索组件", "mode": "component-reuse", "mappingRef": "M03", "mappingStatus": "verified", "target": {"path": "src/components/pro-search/index.vue", "export": "ProSearch"}, "dependencies": ["P001-C01"], "requirements": ["使用XX筛选组件", "补充风险等级、处置状态和时间范围筛选配置"], "states": ["expanded", "collapsed"], "mockContract": {"filterFields": ["风险等级", "处置状态", "时间范围", "事件名称"]}, "acceptanceCriteria": ["筛选条件组合生效"], "prohibitedChanges": []}
        ],
        "mockContract": {"requiredFields": ["事件名称", "风险等级", "处置状态", "发现时间"], "updateAfterActions": ["处置成功后列表、统计卡片和详情状态同步更新"]},
        "stateContract": {"loading": "查询中表格展示loading", "empty": "字段为空展示-", "search-no-result": "搜索无结果展示暂无符合条件的数据"},
        "acceptanceCriteria": ["页面入口可访问", "筛选、分页和行内操作可用", "视觉回归通过"],
        "outOfScope": ["不实现真实后端接口"]
      },
      "children": []
    }
  ],
  "codingGuide": {
    "overviewItems": [
      {"outputItem": "全局复用策略", "description": "说明优先复用哪些页面、组件和功能链路。"},
      {"outputItem": "全局Mock数据策略", "description": "说明整体Mock数据来源、结构和覆盖范围。"},
      {"outputItem": "全局编码边界", "description": "说明不实现真实后端、鉴权、复杂联调等。"},
      {"outputItem": "组件使用规则", "description": "严格按照页面区块、表格字段、表单字段中标注的组件名称开发，不得用原生HTML或其他组件替代；页面模板中已指定的标题栏、筛选区、表格、分页、弹窗、抽屉等组件，应按模板组件骨架实现；字段表中标注为标签、链接按钮、状态徽标、下拉选择、日期范围、开关等组件的内容，必须使用对应iDux或公司封装组件实现；未标注组件名称的普通文本/数字字段，可按常规文本渲染，如实现时发现交互含义，应先回查匹配 Product Design 的 Component 层已登记业务封装，未登记时回查Common Design组件映射表补齐。"},
      {"outputItem": "页面开发顺序", "description": "说明建议先开发哪些页面，后开发哪些页面。"}
    ],
    "overviewMockData": ["至少12条事件数据", "覆盖高/中/低风险", "覆盖待处置/处理中/已处置", "包含1条长事件名称和1条空影响用户数据"],
    "overviewNotes": ["全局筛选逻辑基于Mock数据组合生效", "处置成功后列表、统计卡片和详情状态同步更新", "所有无结果场景展示空状态"],
    "overviewPrompt": "请基于本HTML说明书实现前端Demo，使用Mock数据并完成基础交互逻辑。总览页参考全局复用策略、Mock策略和编码边界，页面级交互与Coding要求参考各页面。"
  }
}
```
