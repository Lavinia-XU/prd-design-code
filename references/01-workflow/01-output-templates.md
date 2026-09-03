# 输出模板汇总

## 目录

1. [对话框输出边界](#1-对话框输出边界)
2. [对话框主输出模板](#2-对话框主输出模板)
3. [HTML说明书生成模板](#3-html说明书生成模板)
4. [AI Coding指导输出格式](#4-ai-coding指导输出格式)
5. [Coding计划执行模板](#5-coding计划执行模板)

## 1. 对话框输出边界

对话框主体输出只到“页面总览表”为止。页面总览表之后必须先输出待确认问题并等待用户确认；用户确认后，才生成HTML说明书。页面总览之后的逐页内容不得在对话框展开。

对话框允许输出：

- 需求概括
- 主要用户角色
- 核心场景与功能映射
- 导航结构
- 页面总览表
- 待确认问题
- HTML文件路径和简短说明

对话框禁止展开：

- 逐页设计说明
- 页面内容区块细节
- Demo交互与逻辑规则明细
- 搜索筛选、二次确认、状态规则、极端情况明细
- Mock数据完整规则
- AI Coding完整提示词

以上禁止展开的内容必须写入HTML。需求颗粒度不足时，先由AI按Product Design、已有代码和常见B端产品模式补齐能保证用户旅程、功能点、数据、操作、状态和页面层级闭环的页面设计，不要把字段命名、按钮文案、普通筛选项、常规表格字段等可合理补齐的细节全部抛给用户确认。页面总览后必须追加待确认问题，控制在10个以内，并只询问会影响整体设计、导航结构、用户旅程闭环、关键业务规则或Coding实现的问题。输出待确认问题后停止，等待用户确认；只有用户确认后才生成HTML说明书。若没有关键待确认问题，明确写“暂无关键待确认问题，按当前页面总览继续生成HTML说明书”，然后可继续生成HTML。

## 2. 对话框主输出模板

```markdown
# <需求名称>设计与编程指导

## 1. 需求概括
<简要概述本需求解决的问题，不限制为一句话>

## 2. 主要用户与场景
### 2.1 主要用户角色
| 用户角色 | 岗位职责 | 核心任务 | 在Demo中关注什么 |
| -------- | -------- | -------- | ---------------- |

### 2.2 核心场景与功能映射
| 核心场景 | 用户要完成的任务 | Demo中对应能力 |
| -------- | ---------------- | -------------- |

## 3. Demo 页面总览
### 3.1 导航结构
<从一级菜单到Tab菜单综合展示本次Demo涉及范围，同一菜单只写一次>

### 3.2 页面总览表
| 业务模块 | 页面ID | 页面名称 | 页面类型 | 页面用途 | 入口方式 | 关键交互 | 初步复用方向 |
| -------- | ------ | -------- | -------- | -------- | -------- | -------- | ------------ |

### 3.3 待确认问题
| 序号 | 待确认问题 | 影响范围 | 当前默认假设 |
| ---- | ---------- | -------- | ------------ |
| 1 | <只填写关键问题；无关键问题时写“暂无关键待确认问题”> | <导航结构/页面容器/用户旅程/业务规则/Coding实现> | <默认假设> |
```

## 3. HTML说明书生成模板

```markdown
# <需求名称>设计与编程指导

## 1. 需求概括
<简要概述，不限制为一句话>

## 2. 核心用户与场景
### 2.1 主要用户角色
| 用户角色 | 岗位职责 | 核心任务 | 在Demo中关注什么 |
| -------- | -------- | -------- | ---------------- |

### 2.2 核心场景与功能映射
| 核心场景 | 用户要完成的任务 | Demo中对应能力 |
| -------- | ---------------- | -------------- |

## 3. Demo 页面总览
### 3.1 导航结构
<从一级菜单到Tab菜单综合展示本次Demo涉及范围，同一菜单只写一次>

### 3.2 页面总览表
| 业务模块 | 页面ID | 页面名称 | 页面类型 | 页面用途 | 入口方式 | 关键交互 | 初步复用方向 |
| -------- | ------ | -------- | -------- | -------- | -------- | -------- | ------------ |

入口方式填写要求：如果页面从导航菜单或Tab进入，写清完整导航路径；如果功能是页面内轻量入口，必须写清所属主页面、触发按钮和打开容器，例如“在策略管理页工具栏点击设置标签，打开抽屉表单页”，不要只写“按钮进入”。页面类型必须来自页面类型决策表中的最终类型，并且该名称必须已存在于实际读取的Common Design、匹配Product Design或已验证代码中；页面类型列必须输出 Common Design 中文页面类型名（如概览表格页、抽屉表单页），禁止输出模板 ID（如 page-table-overview）；不得自行创造未被依据定义的模板名称。若无匹配模板，统一使用“自定义页面类型”，并注明继承模板和差异原因。关键交互中如包含AI补齐内容，需要标注`基于页面目标闭环补齐`。初步复用方向仅可写`复用已有页面`、`参考已有框架`、`新增页面`或`待详细设计确认`；具体开发方式、组件和实现差异在HTML页面级AI Coding指导中确定。

### 3.3 待确认问题
以下问题会影响Demo设计和AI Coding准确性，建议优先确认：

| 序号 | 待确认问题 | 影响范围 | 当前默认假设 |
| ---- | ---------- | -------- | ------------ |
| 1 | <只填写关键问题；无关键问题时写“暂无关键待确认问题”> | <导航结构/页面容器/用户旅程/业务规则/Coding实现> | <默认假设> |

### 3.4 下一步
请先确认或修正以上待确认问题。确认后，我会生成HTML设计说明书；逐页设计说明、页面级交互规则、页面级Coding指导、Mock数据和总结性AI Coding完整提示词将写入HTML，左侧目录按页面层级展示。

<!-- 用户确认后再输出：
如果用户确认内容影响导航结构或页面总览，先重新输出：
### 3.1 更新后导航结构
<按用户确认后的菜单、Tab和页面层级重新输出>

### 3.2 更新后页面总览表
| 业务模块 | 页面ID | 页面名称 | 页面类型 | 页面用途 | 入口方式 | 关键交互 | 初步复用方向 |
| -------- | ------ | -------- | -------- | -------- | -------- | -------- | ------------ |

### HTML设计说明书
- HTML文件：`./<需求名称>-demo-design-spec.html`，输出目录按输出目录判定规则确定：用户明确指定位置时用指定位置；项目根目录存在可确定的 `.demo/design/{hash}/`（`{hash}` 为真实子目录名）时输出到该目录；找不到或无法确定时默认输出到项目根目录。demo-spec.json 与 HTML 同目录输出。目录探测为只读静默检查，未找到目标目录不得报错或中断，直接按项目根目录输出。
- 说明：逐页设计说明、页面级Demo交互与逻辑规则、页面级Coding指导、Mock数据和总结性AI Coding完整提示词已写入HTML。左侧目录按页面层级展示，点击切换后右侧展示对应页面内容。

### Coding计划
HTML设计说明书已生成。请先查看HTML页面内容；如果HTML中有需要调整的页面结构、字段、交互、状态或说明内容，可以直接告知修改点，我会先更新并重新生成最新HTML。HTML 说明书是需用户确认的设计产物，确认后我会自动执行代码映射并输出 Coding Plan，随后直接开始 Coding，不再等待额外确认。

- 导航结构：<明确本次开发页面的导航路径，如一级菜单 / 二级菜单 / 三级菜单 / Tab或页面入口；说明新增路由还是复用已有菜单>。
- 全新开发页面：<列出本次AI全新开发的页面ID、页面名称和容器类型>。
- 参考已有页面开发：<列出会参考的已开发页面、代码模块或目录；无则写“暂无”>。
- 复用已有功能点：<列出会复用的组件、表格、筛选、弹窗、抽屉、Mock数据、状态管理、样式或交互模块；不重新开发的范围要写清楚>。
- 新增实现功能点：<列出需要本次新增编码实现的交互、状态、Mock数据或页面逻辑>。
- 开发顺序：<按页面层级列出先后顺序，先父级主页面，再新增、编辑、详情、弹窗或抽屉等子页面>。

如 HTML 说明书无需调整，我将按以上 Coding Plan 自动开始编码。
-->
```

## 4. AI Coding指导输出格式

页面总览之后，将完整设计说明整理为JSON并调用脚本生成HTML。JSON中不写入`questions`字段；待确认问题只在对话框展示。交互与逻辑规则必须整合进对应页面的`sections`区块说明中，例如工具栏、筛选项、字段展示、可点击操作、状态值、表单选项、校验和边界状态；不再使用独立的页面内关键交互章节或全局交互规则页。每个页面对象必须写入`restoreRequirement`字段，描述从Common Design页面模板获取的页面骨架组件，例如标题栏、筛选区、表格、分页、弹窗、抽屉等，不负责罗列全部字段组件。每个页面对象必须写入`wireframe`字段，用ASCII线框图表达页面标题栏、内容区、关键元素和底部操作；wireframe.ascii 必须严格按所选页面模板（匹配Product Design声明了页面模板时按其模板，否则按Common Design模板）的布局结构绘制出模板必需区域的布局痕迹（标题栏、筛选区、表格、分页、底部操作区等），只允许替换文案并完善内容区中的具体内容，禁止调整模板布局结构、区块顺序、容器形态或新增模板不存在的区域；禁止用一句话或几个字代替线框图，否则被 RULE-32 阻断；regions 声明的内容性区域在 ascii 中无绘制痕迹时触发 RULE-33 提示；必要时写入`wireframeNote`字段说明容器关系、Tab层级或固定底部栏。底部操作区必须继承已读取Common Design页面模板中的容器规则，`wireframe`与`footerActions`中的对齐方式、按钮顺序和规则来源必须一致，不得无依据左右分置按钮。按钮顺序、对齐方式与布局细节一律以已读取 Common Design 页面模板及模板注册表为准，本 Skill 不保存按钮顺序细节。若页面属于分层Tabs页标题，wireframe中的Tab必须与页面标题同一行展示，不得单独下沉为内容区Tab。若页面存在多个内容切换Tab，`wireframe`应按每个Tab分别绘制对应内容区块的线框图，不要只输出一个总线框图；如果页面同时存在步骤条等内容切换控件，也按同样方式处理，按每个步骤分别绘制对应内容区块的线框图。生成HTML说明书前必须执行页面类型一致性自检：`pages`里的页面类型、页面名称和页面层级必须与页面总览一致；若用户未明确要求修改，不得擅自更改页面类型、页面结构或页面名称。配置类页面的表单布局（对齐方式、排列方式、label与组件关系等）一律以已读取 Common Design 表单规范及模板注册表为准，本 Skill 不保存表单布局细节。若页面引用Product Design或已有代码中的功能点实现，页面内容区只简要描述功能点入口、触发效果、展示规则和校验规则，并在页面内`codingGuide.designReferences`和`codingGuide.implementationNotes`中补充关联说明和编码指引。页面内`codingGuide.designReferences`登记本页设计决策的知识来源，每项包含`source`与`ref`：`source`取值`common-design` / `product-design` / `code` / `ai-fill`；`ref`为来源标识（如"Common Design 页面模板: 概览表格页"、"Product Design: 策略配置主题框架"、"已验证代码: src/pages/event-analysis/index.vue"、"AI 补齐: 自动补齐筛选项"）。声称引用 Product Design 或 Common Design 的页面必须在此登记对应来源，无来源的设计决策须标记为 `ai-fill`，否则触发 RULE-40 提示（warning，不校验是否读全）。若需求没有明确筛选条件，页面JSON中的查询区与筛选区说明也必须写明AI的自动补齐结果，包括补充了哪些字段、采用什么控件以及补齐依据。筛选区必须写明使用一个高级搜索组件（组件名以已读取 Common Design 组件映射表为准）还是多个独立组件组合；多个独立组件时，`filterComponent`和`filterComponentDescription`中统一说明各独立组件名称，筛选字段表格不再单独标注iDux组件名称。若筛选项较多或需要组合管理，wireframe 和 sections 中只写“高级搜索框”整体组件，不展开外观，但仍需在高级搜索配置说明和`filterFields`中列出字段和筛选方式。表单字段`formFields`必须在组件类型右侧写`iduxComponent`；表格字段`tableFields`必须写`iduxComponent`，普通文本/数字可留空，标签、链接按钮、状态徽标、操作按钮等非普通文本必须标注组件名称。需求或规范中明确列出的字段（表格列、表单项、筛选项、详情描述字段、配置项等）必须逐项落入对应区块的字段数组（`tableFields`/`formFields`/`filterFields`/`cardFields`/`fields`等），不得过滤、合并或仅简述；页面对象应写入`requirementFieldNames`（需求/规范明确要求的字段名数组）与`excludedFields`（字段名到排除原因的映射），缺失的需求字段会被 RULE-36 阻断。总结性Coding指导写入顶层`codingGuide`，页面级Coding指导写入页面内`codingGuide`。页面层级通过 `pages` 数组平铺全部页面（含弹窗、抽屉）表达；父页面的`children`只写子容器 ID（字符串）用于标注归属，禁止在 children 内嵌完整页面对象（RULE-35 阻断）。每个页面必须写入`navigation`对象，用`primary`、`secondary`、`tertiary`、`tab`分别表示一级导航、二级导航、三级导航和Tab页面；没有对应层级时填空字符串，禁止只用`/`拼接路径。`navigation`表示页面所属菜单或Tab位置，不表示当前功能子页面名称；新增、编辑、详情、弹窗、抽屉等由主页面操作进入的非菜单页面，必须继承所属主页面的`navigation`，不要把“新增xx”“编辑xx”“xx详情”写进导航位置。HTML中的目录开发要求必须写入Coding指导：左侧目录只用于切换页面内容，Coding时不要使用URL hash定位锚点开发目录；该要求属于HTML生成规范，不属于产品Coding实现规范。

### 4.1 脚本调用

```shell
python scripts/generate_demo_spec_html.py --input ./demo-spec.json --output ./demo-design-spec.html

注意：`--output` 按输出目录判定规则确定：存在可确定的 `.demo/design/{hash}/` 时写成该目录下的文件路径；否则写成项目根目录下的文件路径；用户明确指定其他位置时按用户指定路径输出。
```

### 4.2 JSON结构

同步声明：示例 JSON 中的组件名（如 IxTable、IxPagination、IxProSearch 等）与页面类型名仅为格式示例，实际组件名、页面类型与用法一律以已读取 Common Design 组件映射表及页面模板为准；Common Design 更新后以 Common Design 为准，本 Skill 不保存组件映射清单。

```json
{
  "title": "数据防泄密事件分析需求设计说明书",
  "overview": {
    "summary": "本Demo用于展示事件分析、筛选定位、详情查看和处置闭环。",
    "pageOverview": [
      {"module": "事件分析", "id": "P001", "name": "事件列表", "type": "概览表格页", "containerType": "page", "purpose": "查看和筛选事件", "entry": "菜单进入", "interaction": "查看详情、处置、导出", "designSource": "通用设计Skill", "codingMode": "全新开发"}
    ]
  },
  "navigation": [
    {"label": "数据安全", "children": [{"label": "数据防泄密", "children": [{"label": "事件分析"}]}]}
  ],
  "pages": [
    {
      "id": "P001",
      "name": "事件列表",
      "type": "概览表格页",
      "containerType": "page",
      "navigation": {"primary": "数据安全", "secondary": "数据防泄密", "tertiary": "事件分析", "tab": ""},
      "purpose": "帮助安全运维人员查看事件概览并筛选定位风险事件。",
      "layout": "上方概览统计区 + 下方筛选表格区。",
      "operations": [
        {"id": "P001-OP01", "action": "delete", "label": "删除", "trigger": "行内操作", "confirm": true, "confirmConfig": {"title": "确认删除该事件？", "level": "danger"}},
        {"id": "P001-OP02", "action": "refresh", "label": "刷新", "trigger": "页头"}
      ],
      "templateContract": {
        "templateId": "page-table-overview",
        "baseTemplateId": "",
        "navigationType": "left-shaped",
        "navigationTypeStatus": "assumed",
        "navigationTypeSource": "AI补齐",
        "navigationTypeNote": "概览表格页无明确导航依据时默认左侧菜单结构",
        "templateSource": "common-design/references/03-design-template/01-page-types.md#page-table-overview",
        "requiredRegions": ["global-navigation", "title-bar", "overview", "filter", "toolbar", "table", "pagination"],
        "optionalRegions": [],
        "regionOrder": ["global-navigation", "title-bar", "overview", "filter", "toolbar", "table", "pagination"],
        "footerContract": {"required": false, "alignment": "", "buttonOrder": []},
        "componentContract": {"overview": ["IxCard"], "table": ["IxTable"], "pagination": ["IxPagination"]},
        "wireframeContract": {"variantsRequired": false},
        "override": {"enabled": false, "source": "", "reason": "", "affectedRules": []}
      },
      "restoreRequirement": {"description": "按Common Design概览表格页模板还原页面骨架，组件信息来自页面模板推荐组件。", "components": [{"area": "标题栏", "iduxComponent": "页面模板指定标题栏组件", "source": "Common Design页面模板", "usage": "承载页面标题和导出、刷新等页面级操作"}, {"area": "筛选区", "iduxComponent": "IxProSearch", "source": "Common Design页面模板", "usage": "承载事件查询条件"}, {"area": "表格", "iduxComponent": "IxTable", "source": "Common Design页面模板", "usage": "承载事件列表字段和行内操作"}, {"area": "分页", "iduxComponent": "IxPagination", "source": "Common Design页面模板", "usage": "承载列表分页"}]},
      "wireframeNote": "线框图先继承概览表格页模板，再填入事件分析的业务内容；布局来源为已读取的Common Design页面模板。",
      "wireframe": {
        "templateId": "page-table-overview",
        "navigationType": "left-shaped",
        "layoutSource": "Common Design page-table-overview",
        "shell": {"globalNavigation": true, "titleBar": {"required": true, "type": "plain", "component": "页面模板指定标题栏组件"}, "contentContainer": {"required": true, "type": "page-content"}, "footer": {"required": false, "alignment": "", "height": "56px"}},
        "regions": [
          {"id": "global-nav", "templateRegion": "global-navigation", "position": "top", "required": true, "content": "全局导航"},
          {"id": "title-bar", "templateRegion": "title-bar", "position": "top", "required": true, "content": "页面标题行：事件分析 [导出] [刷新]"},
          {"id": "overview", "templateRegion": "overview", "position": "content-top", "required": true, "content": "概览统计区：事件总数 | 待处置 | 高风险"},
          {"id": "filter", "templateRegion": "filter", "position": "content", "required": true, "content": "筛选工具栏：风险等级 时间范围 关键字 [查询]"},
          {"id": "table", "templateRegion": "table", "position": "content", "required": true, "content": "表格区：事件名称 | 风险等级 | 发现时间 | 操作"},
          {"id": "pagination", "templateRegion": "pagination", "position": "bottom", "required": true, "content": "分页区：上一页 1 2 3 下一页"}
        ],
        "variants": [],
        "ascii": "┌──────────────────────────────────────────────┐\n│ 事件分析                        [导出] [刷新] │\n├──────────────────────────────────────────────┤\n│ ┌──────────────────────────────────────────┐ │\n│ │ 事件总数  待处置  高风险  已处置           │ │\n│ └──────────────────────────────────────────┘ │\n│ [风险等级] [时间范围] [关键字]       [查询]  │\n│ [导出]                                      │\n│ ┌──────────────────────────────────────────┐ │\n│ │ 事件名称 | 风险等级 | 发现时间 | 操作     │ │\n│ │ 事件A    | 高       | 08-01    | 详情     │ │\n│ └──────────────────────────────────────────┘ │\n│ 上一页 1 2 3 下一页     共 42 条             │\n└──────────────────────────────────────────────┘"
      },
      "sections": [
        {"title": "概览统计区", "type": "指标区", "description": "页面顶部横向卡片展示事件总数、待处置事件数、高风险事件数。高风险事件数为可点击数字，点击后下方表格筛选风险等级为高，统计卡片保持高亮反馈。", "fields": ["事件总数：数字，0值正常展示", "待处置事件数：可点击数字，点击筛选处置状态为待处置", "高风险事件数：可点击数字，点击筛选风险等级为高"], "actions": ["点击高风险事件数后，列表筛选高风险事件"], "interactionNotes": ["点击统计数字后刷新表格数据并同步筛选条件", "查询中表格展示loading"], "validationRules": ["无数据时统计数字展示0，不隐藏卡片"]},
        {"title": "事件表格区", "type": "表格区", "description": "位于概览统计区下方，承载事件查询、导出和单条事件操作。", "toolbar": ["导出按钮", "风险等级下拉多选", "时间范围选择器", "事件名称输入框"], "filterComponent": "IxProSearch", "filterComponentDescription": "使用一个高级搜索组件承载风险等级、发现时间和事件名称筛选；若改为平铺筛选，则在filterComponent中统一列出各独立iDux组件名称。", "filterFields": [{"name": "风险等级", "component": "下拉多选", "mode": "多选", "options": "高/中/低", "default": "全部", "description": "按风险等级筛选"}, {"name": "发现时间", "component": "日期范围", "mode": "范围", "options": "最近7天/最近30天/自定义", "default": "最近7天", "description": "按发现时间筛选"}, {"name": "事件名称", "component": "输入框", "mode": "模糊搜索", "options": "-", "default": "空", "description": "按事件名称搜索"}], "tableFields": [{"name": "事件名称", "display": "可点击文本", "iduxComponent": "IxButton link", "description": "点击打开事件详情抽屉；长文本单行省略并悬浮展示完整内容"}, {"name": "风险等级", "display": "单标签", "iduxComponent": "IxTag", "description": "高/中/低，使用红/橙/蓝标签"}, {"name": "发现时间", "display": "时间", "iduxComponent": "", "description": "普通文本展示，支持排序"}], "actions": ["查询：按条件刷新表格", "重置：清空条件并恢复默认列表"], "interactionNotes": ["点击事件名称打开详情抽屉"], "validationRules": ["搜索无结果展示暂无符合条件的数据"]}
      ],
      "footerActions": {"visible": false, "containerType": "page", "alignment": "none", "actions": [], "source": "无底部操作"},
      "codingGuide": {
        "pageContext": {
          "pageId": "P001",
          "pageType": "标准列表页",
          "route": "/data-security/event-analysis",
          "codeAvailability": "verified",
          "visualBaselineRef": "src/pages/event-analysis/index.vue"
        },
        "implementationRules": [
          "优先复用已验证页面和业务组件",
          "严格使用页面字段表中指定的组件",
          "不得用原生 HTML 替代业务组件"
        ],
        "designReferences": [
          {"source": "product-design", "ref": "Product Design: 事件分析主题框架"},
          {"source": "common-design", "ref": "Common Design 页面模板: 概览表格页"},
          {"source": "code", "ref": "已验证代码: src/pages/event-analysis/index.vue"},
          {"source": "ai-fill", "ref": "AI 补齐: 自动补齐筛选项"}
        ],
        "pageItems": [
          {"id": "P01-C01", "scope": "page-shell", "name": "页面框架", "mode": "reuse-framework", "mappingRef": "M01", "mappingStatus": "verified", "target": {"path": "src/pages/event-analysis/index.vue", "export": "EventAnalysisPage"}, "sourceRefs": ["page:P01", "mapping:M01"], "dependencies": [], "requirements": ["复用事件分析页整体布局和固定字段", "新增概览统计区和事件表格区", "保留标题栏、筛选区、表格、分页结构"], "states": ["loading", "empty", "search-no-result", "error"], "mockContract": {"requiredFields": ["事件名称", "风险等级", "发现时间"], "updateAfterActions": ["查询后刷新列表"]}, "acceptanceCriteria": ["页面入口可访问", "页面结构与视觉参考页面一致", "筛选、分页和行内操作可用"], "prohibitedChanges": ["不得替换已验证的业务表格容器", "不得引入真实后端接口"]},
          {"id": "P01-C02", "scope": "toolbar", "name": "导出功能", "mode": "direct-reference", "mappingRef": "M02", "mappingStatus": "verified", "target": {"path": "src/components/export-btn/index.vue", "export": "ExportButton"}, "sourceRefs": ["page:P01", "section:toolbar"], "dependencies": ["P01-C01"], "requirements": ["复用已开发好的导出实现", "仅替换导出字段和文案"], "states": ["exporting", "export-success", "export-failed"], "mockContract": {"exportFields": ["事件名称", "风险等级", "发现时间"]}, "acceptanceCriteria": ["导出文件字段与列表一致", "导出中按钮展示loading"], "prohibitedChanges": ["不得新增真实导出接口"]},
          {"id": "P01-C03", "scope": "filter", "name": "筛选搜索组件", "mode": "component-reuse", "mappingRef": "M03", "mappingStatus": "verified", "target": {"path": "src/components/pro-search/index.vue", "export": "ProSearch"}, "sourceRefs": ["page:P01", "section:filter"], "dependencies": ["P01-C01"], "requirements": ["使用IxProSearch承载筛选", "补充风险等级、时间范围和事件名称筛选配置"], "states": ["expanded", "collapsed"], "mockContract": {"filterFields": ["风险等级", "发现时间", "事件名称"]}, "acceptanceCriteria": ["筛选条件可配置", "重置恢复默认列表"], "prohibitedChanges": ["不得替换为平铺筛选"]}
        ],
        "mockContract": {"requiredFields": ["事件名称", "风险等级", "发现时间"], "updateAfterActions": ["查询后刷新列表"]},
        "stateContract": {"loading": "查询中展示loading", "empty": "无数据显示空状态", "search-no-result": "搜索无结果展示暂无符合条件的数据"},
        "acceptanceCriteria": ["页面入口可访问", "视觉回归通过", "筛选、分页和行内操作可用"],
        "outOfScope": ["不实现真实后端接口", "不实现真实鉴权"]
      },
      "children": []
    }
  ],
  "codingGuide": {
    "overviewItems": [
      {"outputItem": "全局复用策略", "description": "说明优先复用哪些页面、组件和功能链路。"},
      {"outputItem": "全局Mock数据策略", "description": "说明整体Mock数据来源、结构和覆盖范围。"},
      {"outputItem": "全局编码边界", "description": "说明不实现真实后端、鉴权、复杂联调等。"},
      {"outputItem": "组件使用规则", "description": "严格按照页面区块、表格字段、表单字段中标注的组件名称开发，不得用原生HTML或其他组件替代；页面模板中已指定的标题栏、筛选区、表格、分页、弹窗、抽屉等组件，应按模板组件骨架实现；字段表中标注为标签、链接按钮、状态徽标、下拉选择、日期范围、开关等组件的内容，必须使用对应iDux或公司封装组件实现；未标注组件名称的普通文本/数字字段，可按常规文本渲染，如实现时发现交互含义，应回查Common Design组件映射表补齐。"},
      {"outputItem": "页面开发顺序", "description": "说明建议先开发哪些页面，后开发哪些页面。"}
    ],
    "overviewMockData": ["至少12条事件数据，覆盖高/中/低风险和待处置/处理中/已处置状态"],
    "overviewNotes": ["筛选基于Mock数据实时生效", "提交处置后更新当前行状态", "左侧目录用于切换页面内容，不要使用URL hash定位锚点开发目录。"],
    "overviewPrompt": "请基于本HTML说明书实现前端Demo，使用Mock数据并完成基础交互逻辑；总览页参考全局复用策略、Mock策略和编码边界，页面级交互与Coding要求参考各页面。"
  }
}
```

### 4.1 多内容 Tab 页面示例

页面声明两个及以上内容 Tab 时，必须为每个 Tab 提供对应的 wireframe variant，并通过 tabId 关联；sections 绑定 tabId 便于 sections、tabs、variants、wireframe.regions 互相追踪。校验规则见 04-demo-output-spec.md 第 11.3 节。

```json
{
  "id": "P005",
  "name": "主机详情",
  "type": "抽屉详情页",
  "containerType": "drawer",
  "tabs": [
    {"tabId": "tab-overview", "name": "概览"},
    {"tabId": "tab-source", "name": "来源与识别依据"},
    {"tabId": "tab-log", "name": "操作记录"}
  ],
  "operations": [
    {"id": "OP01", "action": "open-container", "label": "打开详情抽屉", "trigger": "表格行内操作",
     "targetPageId": "P005", "targetContainerType": "drawer", "confirm": false,
     "note": "从列表行内操作进入详情抽屉"}
  ],
  "wireframe": {
    "templateId": "page-detail-drawer",
    "variants": [
      {"tabId": "tab-overview", "preserveRegions": ["title-bar", "object-summary", "tab-bar", "drawer-footer"],
       "changedRegions": ["tab-content"], "ascii": "┌────────────────────────────────┐\n│ 标题栏：主机详情          [关闭] │\n├────────────────────────────────┤\n│ 对象摘要：主机A 10.0.0.1          │\n├────────────────────────────────┤\n│ Tab行：概览 | 来源 | 操作记录     │\n├────────────────────────────────┤\n│ 概览内容：                        │\n│ 主机名  主机A                     │\n│ IP      10.0.0.1                  │\n├────────────────────────────────┤\n│                    [关闭]  │\n└────────────────────────────────┘"},
      {"tabId": "tab-source", "preserveRegions": ["title-bar", "object-summary", "tab-bar", "drawer-footer"],
       "changedRegions": ["tab-content"], "ascii": "┌────────────────────────────────┐\n│ 标题栏：主机详情          [关闭] │\n├────────────────────────────────┤\n│ 对象摘要：主机A 10.0.0.1          │\n├────────────────────────────────┤\n│ Tab行：概览 | 来源 | 操作记录     │\n├────────────────────────────────┤\n│ 来源内容：                        │\n│ 来源类型  自动识别                │\n│ 识别规则  资产指纹                 │\n├────────────────────────────────┤\n│                    [关闭]  │\n└────────────────────────────────┘"},
      {"tabId": "tab-log", "preserveRegions": ["title-bar", "object-summary", "tab-bar", "drawer-footer"],
       "changedRegions": ["tab-content"], "ascii": "┌────────────────────────────────┐\n│ 标题栏：主机详情          [关闭] │\n├────────────────────────────────┤\n│ 对象摘要：主机A 10.0.0.1          │\n├────────────────────────────────┤\n│ Tab行：概览 | 来源 | 操作记录     │\n├────────────────────────────────┤\n│ 操作记录内容：                    │\n│ 时间 | 操作人 | 操作内容          │\n│ 08-01 | admin   | 更新配置        │\n├────────────────────────────────┤\n│                    [关闭]  │\n└────────────────────────────────┘"}
    ]
  },
  "sections": [
    {"title": "概览", "type": "overview", "tabId": "tab-overview", "fields": ["主机名", "IP", "操作系统"]},
    {"title": "来源与识别依据", "type": "descriptions", "tabId": "tab-source", "fields": ["来源类型", "识别规则"]},
    {"title": "操作记录", "type": "timeline", "tabId": "tab-log", "fields": ["操作人", "操作时间", "操作内容"]}
  ]
}
```

要点：
- `tabs` 中 `tabId` 唯一；`variants` 数量与 `tabs` 一致，每个 variant 通过 `tabId` 关联对应 Tab，不允许孤立 variant。
- 每个 variant 的 `preserveRegions` 必须保留公共页面外壳（标题栏、对象摘要、Tab 行、底部操作区），`changedRegions` 声明当前 Tab 内容区，`ascii` 绘制完整内容区线框图。
- 单内容 Tab 或普通详情页不要求 variants，仍可使用单张 wireframe。

## 5. Coding计划执行模板

### 5.1 HTML生成后的询问

```text
HTML设计说明书已生成。请先查看HTML页面内容；如果HTML中有需要调整的页面结构、字段、交互、状态或说明内容，可以直接告知修改点，我会先更新并重新生成最新HTML。HTML 说明书是需用户确认的设计产物，确认后我会自动执行代码映射并输出 Coding Plan，随后直接开始 Coding，不再等待额外确认。
```

### 5.2 Coding计划输出

```text
- 总览AI Coding指导：<写全局复用策略、全局Mock数据要求、全局编码边界、全局一致性要求和页面开发顺序>。
- 页面级AI Coding指导：<按每个页面列出编号、开发对象、开发方式、复用与代码映射、实现要求、完成判定；例如页面框架、导入/导出、资产选择器、筛选组件、表单、弹窗、抽屉等>。
- 参考已有页面开发：<列出会参考的已开发页面、代码模块或目录；无则写“暂无”>。
- 开发顺序：<按页面层级列出先后顺序，先父级主页面，再新增、编辑、详情、弹窗或抽屉等子页面>。

如 HTML 说明书无需调整，我将按以上 Coding Plan 自动开始编码。
```
```
