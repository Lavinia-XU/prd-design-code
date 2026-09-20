# Demo输出规格

## 目录

1. [HTML逐页设计说明](#8-html逐页设计说明)
2. [HTML说明书结构](#9-html说明书结构)
3. [自检规则](#10-自检规则)
4. [设计闭环自动校验](#11-设计闭环自动校验)

## 8. HTML逐页设计说明

### 8.1 逐页内容描述

每个页面按以下结构写入HTML说明书。HTML视觉层级必须明确：页面标题使用24号；页面目标、页面基础信息、页面内容区块、底部操作、页面级AI Coding指导等一级小标题使用18号；页面内容区块名称使用16号；字段、按钮/可点击操作、展示形式与取值范围、交互反馈、校验边界等三级小标题使用14号；正文、列表、表格内容使用12号。

```markdown
## 页面ID-页面名称

## 页面类型

<填写页面类型，如基础表格页、表单抽屉、自定义页面类型等>

## 页面内容区块

先整体说明页面内不同内容区块之间的位置关系，并遵守该页面类型已定义好的方位位置，不要自行组合新的上下左右关系，避免把页面结构弄混。若页面内有明显白色卡片承载内容，按卡片划分；若没有明显卡片，按业务内容模块划分。若页面有多个内容区块，按先上后下、先左后右逐个描述区块，让读者通过区块描述即可看出页面设计结构关系。

实际输出时应根据页面结构完整列出所有区块，不限于表格区和表单区；常见区块还包括概览区、详情信息区、图表区、操作区、步骤条、提示说明区等。区块划分要确保业务完整性，不要为了套格式把同一个业务对象的工具栏、筛选和列表拆散。**例外（复用业务组件容器）**：拆解出来的容器若命中 Product Design 业务封装组件（或代码识别已知业务封装）且属于需求延伸容器，则**不在本说明书单独描述该页面**——不写页面内容区块、不画线框图、不写底部操作，只在宿主页面的内容区块/线框图中写一句"点击 X 打开 Y（复用 <组件名>，不单独绘制）"，并把该组件登记为开发项与设计依据；自绘样式会与业务实现不一致、误导编码（详见 11.24 RULE-59，声明复用后又自绘会被 REUSE_CONTAINER_OVER_DESCRIBED 阻断）。以下仅为区块描述格式示例，不代表页面只能包含这些区块。生成HTML的JSON中，表格字段必须使用`tableFields`数组，表单字段必须使用`formFields`数组，脚本会将二者渲染为HTML表格；不要把表格字段或表单字段只写成普通`fields`文本列表。字段内容必须写在对应形态渲染的键上（表单字段用`rules`/`tips`，筛选项用`options`/`description`，表格字段用`display`/`description`，键对照见本文件“字段形态键对照（RULE-41）”小节），跨形态套键会导致HTML对应列静默空白并被RULE-41阻断。需求或规范中明确列出的字段（表格列、表单项、筛选项、详情描述字段、配置项等）必须逐项落入对应区块的字段数组，不得过滤、合并或仅简述；页面对象写入`requirementFieldNames`（需求/规范明确要求的字段名数组）与`excludedFields`（字段名到排除原因的映射），校验器以 RULE-36 检查需求字段是否全部落位，缺失字段阻断生成。带固定选项的下拉类字段（表单下拉、筛选下拉及单选/多选等枚举控件）必须把选项逐项完整列出，禁止用“等/例如/…”只举例；页面对象写入`requirementOptionSets`（字段名到完整选项列表的声明），校验器以 RULE-48 检查声明选项是否全部落入表单`rules`或筛选`options`单元格（缺失阻断），并对未声明选项集的选择类字段做截断指纹告警（详见本文件 11.13）。需求源枚举表含分组/层级列时（`requirementOptionSets[].dimension=group/hierarchy`，或 `sourceColumns` 声明 ≥2 列自动视为分组）必须在选项单元格保留该维度（“组名：选项A/选项B”或“父级 → 子级”），压平为单层列表会被 RULE-48 以 OPTION_DIMENSION_LOST 告警；承载该维度的控件形态不在此判定，按 RULE-54 依 Common Design widget patterns（`03-patterns/07-widget-patterns/`）判定并锚点级登记依据。

### Wireframe / ASCII 线框图

每个页面在页面内容区块之后，必须补充`Wireframe / ASCII 线框图`，用于表达页面整体结构、主要区块、展示元素和操作区域。线框图不是视觉稿，不要求像素级精确，但必须让AI Coding能看懂页面容器关系、布局层级、关键字段、状态信息和按钮位置。若页面存在多个内容切换Tab，必须按每个Tab分别绘制对应内容区块的线框图，不要只画一个总图；如果页面同时存在步骤条等内容切换控件，也按同样方式处理，按每个步骤分别绘制对应内容区块的线框图。若是标题栏里的分层Tabs页标题，Tab仍然必须和标题同一行展示，不能下沉到内容区。

生成HTML的JSON中，wireframe必须使用结构化对象作为唯一可信来源，不能只写自由文本；纯字符串wireframe仅作为legacy输入，进入兼容模式警告，strict模式下禁止生成HTML。结构化wireframe至少包含：

- `templateId`、`navigationType`、`layoutSource`：绑定标准页面模板与导航类型；
- `shell`：`globalNavigation`、`titleBar`（required/type/component）、`contentContainer`、`footer`（required/alignment/height）等页面外壳属性；
- `regions`：区域数组，每项包含`id`、`templateRegion`（对应模板必需区域）、`position`、`required`、`component`、`content`；
- `variants`：多步骤或Tab页面必须输出主结构图和每个步骤/Tab一张完整变体图，每张变体包含`preserveRegions`（保留公共外壳区域）与`changedRegions`（变化区域）及`ascii`。

每个页面必须同时填写`templateContract`（templateId/baseTemplateId/templateBase/productTemplateRef/navigationType/templateSource/requiredRegions/optionalRegions/regionOrder/footerContract/componentContract/wireframeContract/override），与结构化wireframe形成闭环；`componentContract` 除按区域声明骨架/字段组件外，须用 `patternComponents` 承载 Pattern 层（如筛选方式 Pattern）算出的组件结论，每项含 `when` / `components` / `source` / `ability`，并同步登记 `codingGuide.designReferences` 的对应 ability 依据，不得使 Pattern 结论遗留在 Pattern 层；`templateBase`取值`common`（默认，模板结构与线框样式继承 Common Design 页面模板）或`product`（匹配 Product Design 声明该页模板 override，模板结构与线框样式以 Product Design 页面模板为准）；`templateBase=product` 时必须填写`productTemplateRef`，指向 Product Design 页面模板文档原文锚点（格式`<文档路径>#<章节/模板条目>`）；模板结构、覆盖范围、必需区域、区域顺序与 footer 契约结论必须基于模板文档原文精读得出并登记到`codingGuide.designReferences`，禁止仅凭索引、摘要或他方转述下结构结论；页面type、templateId、layout、sections、wireframe、footerActions、componentContract和codingGuide必须一致，禁止出现模板结构与线框结构冲突。模板注册表见references/02-template-contracts/common-design-template-registry.json，生成HTML前由scripts/validate_demo_spec.py自动校验，校验失败阻断HTML生成。页面模板 ID 取值口径（强制）：`templateId` 只允许两种写法——①当前模板注册表中的标准模板 ID（无论最终以 Common Design 还是 Product Design 为准，底层结构均取该标准模板，Product Design 覆盖用`templateBase=product`+非空`productTemplateRef`表达）；②`custom`（Product Design 在标准模板之外自定义了页面模板时：`templateId="custom"`+`baseTemplateId`填最接近的当前注册表标准模板 ID+`override.enabled=true`+`override.source`写明 Product Design 模板出处+`override.reason`+`override.affectedRules`，并同步填写`templateBase=product`与非空`productTemplateRef`）。禁止把 Product Design 自定义模板 ID 直接写入`templateId`（RULE-04 以 TEMPLATE_NOT_REGISTERED 阻断），禁止把 Product Design 自定义页面类型名写入页面`type`（RULE-06 以 UNREGISTERED_TYPE 阻断）；页面类型中文名一律以当前模板注册表`name`为准（历史名"步骤条配置页""仪表盘页"已分别改为"下钻步骤条配置页"与"Dashboard"，旧名废弃）。历史旧模板 ID（`page-list-modal`/`page-list-drawer`/`page-detail-drawer`/`page-detail-log`/`page-form-modal`/`page-form-drawer`）仅作兼容识别（RULE-43 覆盖判定自动归一为当前 ID），不得作为新产出；出现在`templateSource`/`layoutSource`/组件来源等模板引用文本中会被 RULE-56 以 LEGACY_TEMPLATE_ID_REF 告警。

HTML说明书中的线框图部分只展示对确认页面结构有用的内容：先展示完整ASCII线框图，线框图下方再补充线框说明（wireframeNote）、线框图结构依据和线框变体；线框变体必须包含对应步骤/Tab的`ascii`线框图才展示，缺少线框图的变体不输出。模板契约（templateId、navigationType、templateSource、模板必需区域、区域顺序、底部操作契约）不属于面向用户的线框图展示内容，移入页面级AI Coding指导作为AI Coding的结构化输入；`regions`数组仅用于模板契约校验与区域一致性检查，不渲染为表格展示；区域对应的组件和内容由页面内容区块（sections）承载。

线框图布局必须参考已读取的Common Design页面模板，以及用户资料、Product Design或已有代码中明确的页面类型结构；仅当已读取规则没有覆盖时，才根据页面目标选择常见B端页面骨架，再补充标题栏、表格工具栏等通用部件，最后填入当前业务元素。底部操作区的位置、按钮顺序和布局必须继承当前页面类型或容器形态对应的Common Design模板；除非PRD、用户确认或匹配Product Design明确覆盖，不得将同一操作区按钮拆分为左右两侧，也不得混用不同容器的布局规则。按钮顺序、必需区域、区域顺序、容器形态等具体设计规则一律以已读取的 Common Design 页面模板及模板注册表为准（见 references/02-template-contracts/common-design-template-registry.json），本 Skill 不保存按钮顺序与模板结构细节。

线框图必须包含：

- 顶部标题栏：页面标题、状态徽标、页面级快捷操作；标题栏必须根据页面进入方式和页面层级选择基础标题栏、下钻页标题栏或分层 Tabs 页标题。
- 中间内容区：筛选区、工具栏、表单分区、表格字段、状态展示、描述列表、概览卡片、提示说明、主要按钮。
- 底部按钮区：保存、取消、提交、下一步、关闭等页面级操作；若为页面级sticky操作栏，需要与内容区分离。
- 必要的层级说明：尤其是Tab、卡片、弹窗、抽屉、下钻页、底部固定栏等容易混淆的容器关系。

生成HTML的JSON中，页面级线框图写入页面对象的`wireframe`字段；如需解释容器关系，写入`wireframeNote`字段。脚本会将其渲染为HTML里的“Wireframe / ASCII 线框图”卡片。

#### 示例：Tab配置表单页线框图

层级说明：该示例按配置表单页结构绘制，标题栏采用分层Tabs页标题；页面标题、纵向分割线和Tab在同一行展示；Tab下方内容区为独立容器，内容区不嵌套在Tab容器内；表单配置内容区与底部按钮区属于同一个配置表单页主容器，底部按钮区高度约56px且按钮左对齐，默认按钮示例为[保存]。

```text
┌──────────┬──────────────────────────────────────────────────────────────┐
│          │ 分层 Tabs 页标题（同一行，紧贴左侧导航）                      │
│          │ LDAP 企业身份 │ 连接配置   组织树   人员导入                  │
│  左侧    ├──────────────────────────────────────────────────────────────┤
│  深色    │ ↓ 间距 8px                                                   │
│  导航    │ ┌────────────────────────────────────────────────────────┐  │
│          │ │ 表单配置内容区                                         │  │
│          │ │ (左右 20px + 卡片 12px = 视觉总间距 32px)              │  │
│          │ │                                                        │  │
│          │ │ 分区标题# 服务器配置                                   │  │
│          │ │ 配置名称      [________________________](带字数计数)   │  │
│          │ │ 服务器地址    [________________________ *]             │  │
│          │ │ 端口            [____]                             │  │
│          │ │ 连接协议        LDAPv3● LDAPv2○ LDAPSv3○             │  │
│          │ │ 企业目录根范围 [________________________________ *]    │  │
│          │ │ 用户查询范围   [________________________________ *]    │  │
│          │ │ OU 查询范围    [________________________________ *]    │  │
│          │ │ 连接账号      [________________________ *]             │  │
│          │ │ 连接凭证      [•••••••••] [重置]                       │  │
│          │ │               [测试连接]                               │  │
│          │ │                                                        │  │
│          │ │ ↓ 间距 8px                                             │  │
│          │ │ 分区标题# 同步设置                                     │  │
│          │ │ 自动全量同步周期 [ 6 ] 小时                            │  │
│          │ │ 启用/禁用        [开关]                                │  │
│          │ │ 最近一次同步     ●成功 2026-08-05 14:32:00 [查看原因]  │  │
│          │ │ 手动同步         [手动同步]（同步中显示进度）           │  │
│          │ │                                                        │  │
│          │ │ 说明：平台仅支持一个外部身份源 / LDAP只读不回写         │  │
│          │ ├────────────────────────────────────────────────────────┤  │
│          │ │ 底部按钮区 (56px，按钮左对齐)                          │  │
│          │ │ [保存]                                                 │  │
│          │ └────────────────────────────────────────────────────────┘  │
│          │         ← 12px →                              ← 12px →     │
└──────────┴──────────────────────────────────────────────────────────────┘
```

表单独列口径（强制，RULE-57）：表单配置项必须**每行一个配置项**，label 在左、控件在右、水平同一行；禁止把两个配置项画在同一行（如上例"端口"与"连接协议"必须分两行）。表单布局真值以已读取的 Common Design 表单规范为准，须锚点级登记到 `codingGuide.designReferences` 并在 `readLedger` 命中 `status=read`；线框出现一行多配置项给 `FORM_LAYOUT_MULTI_COLUMN`（warning），label 与控件不在同一行给 `FORM_LAYOUT_LABEL_NOT_INLINE`（warning），表单布局依据未登记或未精读给 `FORM_LAYOUT_BASIS_UNREAD`（warning）。详见 11.22 表单单列布局闭环（RULE-57）。

#### 示例：表单单列（表单弹窗 / 表单抽屉）

容器形态（弹窗/抽屉）不改变表单布局口径：容器内仍是"每行一个配置项"。

```text
┌──────────────────────────────────────────────┐
│ 新建策略                              关闭 × │
├──────────────────────────────────────────────┤
│ 表单配置内容区（单列）                        │
│ 策略名称      [________________ *]            │
│ 生效范围      [请选择          ▾]             │
│ 优先级        [___]                           │
│ 生效时间      [2026-08-05 00:00]              │
├──────────────────────────────────────────────┤
│                        [确定] [取消]          │
└──────────────────────────────────────────────┘
```

### 示例：表格区

先说明表格区在页面中的相对位置、承载对象和主要操作，再按以下格式描述表格。表格上方的按钮区、筛选区和搜索区通常属于表格工具栏 toolbar，不单独拆成多个区块，而是跟随表格作为一个表格区描述。表格不仅要说明字段，还要说明每个字段的展示形式；默认展示形式为普通文本，也可以根据字段含义使用单标签、多标签、数字、可点击文本、可点击数字、图标+文字等形式。

- 表格工具栏：<按从左到右顺序说明按钮、筛选项和搜索项，如新增、批量删除、状态下拉单选、时间范围选择器、关键字输入框>
- 筛选区说明：先判断筛选方式来源，再判断筛选组件类型并描述筛选字段。
  - 如果Product Design中已经明确该业务、该页面或相似模块使用的筛选方式，必须以Product Design为准，不得自行改成其他筛选方式。
  - 如果Product Design没有说明，再根据页面复杂度判断使用平铺筛选或高级搜索框。
  - 平铺筛选：适合筛选项较少或需要高频操作的列表页；在筛选区组件说明中统一列出各独立组件名称（组件名来源见本节末“组件名来源规则”），筛选字段表格不再单独标注iDux组件名称，但需说明选项范围、默认值和匹配方式。
  - 高级搜索框：适合筛选项较多、不适合全部平铺展示的列表页；必须说明使用一个高级搜索组件（组件名来源见本节末“组件名来源规则”）承载整体筛选；内部字段不展开控件外观，筛选字段表格不再单独标注iDux组件名称，只需说明每个字段的筛选方式，例如单选、多选、模糊搜索、精确搜索、时间范围筛选。
  - 当需求没有明确筛选条件时，优先根据表格字段语义自动补充查询区；不要因为需求未提到筛选条件就默认不设置筛选。自动补齐的筛选项控件类型按本节末“组件名来源规则”确定，本 Skill 不枚举组件映射规则；若字段不足以明确判断，至少补齐名称搜索、状态筛选和时间筛选。对于这类自动补齐的筛选项，需要在页面说明和页面级Coding指导里写明补齐的字段、控件类型和补齐依据，避免被误认为遗漏。若筛选项较多或需要组合管理，应在页面说明中直接使用“高级搜索框”整体描述，不要逐项展开内部筛选字段。
  - 组件名来源规则：匹配 Product Design 且其 Component 层（或 coverage 中 capability 为 `component` / `pattern` 的能力）已登记该业务封装组件时，组件名与用法以 Product Design 业务组件为准，并须在页面 `codingGuide.designReferences` 登记 `source=product-design` 与对应 `ability`（未登记以 RULE-43 `ABILITY_SOURCE_NOT_REGISTERED` 阻断）；Product Design 未登记该能力时，以已读取 Common Design 组件映射表（`common-design/references/05-components/idux-component-map.md`）为准；两者均未覆盖时，标注为 AI 补齐的语义级能力描述。Product Design 已登记的 Component Reference 优先于 Common Design 通用组件，严禁一律写死为 Common Design 通用组件。组件**形态（variant）**的来源分两层、各管一段：**命名/枚举真值**以已读取的 Common Design 组件映射（`common-design/references/05-components/idux-component-map.md`，按组件锚点精读）为准——当某组件登记了多种形态（如 IxTag 的多种标签样式、IxSelect 下拉面板的搜索/新增/树/分组、单选/多选的 radio/卡片）时，须在字段 `iduxComponentForm` 写明本页选用的形态，并以 `formCandidates` 登记该组件在 Common Design 中的形态候选；**选择依据真值**以 Common Design widget patterns（`common-design/references/03-patterns/07-widget-patterns/`，按“目录级索引 + 命中控件对应文件精读”读取，Product Design 侧 pattern 文档同等可用）为准，判定依据须锚点级登记到页面 `codingGuide.designReferences` 且在 `readLedger` 命中 `status=read`（RULE-54，warning 级）。缺组件映射依据或依据未精读命中、缺 widget pattern 选择依据或依据未精读命中，分别告警 `COMPONENT_FORM_SOURCE_UNREAD`、`COMPONENT_FORM_RULE_UNREAD`；单形态组件留空 `formCandidates` 即可、零负担。禁止凭直觉自造形态，禁止未读 widget patterns 判定依据就选定形态。
- 表格字段：

| 字段名称 | 展示形式 | 组件名称 | 说明 |
| -------- | -------- | -------- | ---- |
| <字段1> | 普通文本 |  | <普通文本或数字可不写组件名称；说明字段含义、取值范围、是否可排序或空值展示规则> |
| <字段2> | 单标签/多标签 | <组件名：匹配 Product Design 已登记业务封装时以其为准，否则以 Common Design 组件映射表为准> | <状态值范围、标签颜色、状态含义或标签数量规则，例如在线/离线/告警> |
| <字段3> | 可点击文本/可点击数字 | <组件名：匹配 Product Design 已登记业务封装时以其为准，否则以 Common Design 组件映射表为准> | <点击后跳转详情、打开抽屉或打开明细列表，并说明打开容器和页面反馈> |
| <字段4> | 图标+文字 | <对应图标/徽标组件> | <图标表达含义、文字内容和悬浮说明> |

- 行内操作：<说明操作项顺序和点击结果，如查看打开详情抽屉、编辑打开表单抽屉、删除弹出二次确认；同时说明成功/失败反馈、数据变化和状态联动>
- 搜索与筛选说明：<先说明筛选方式来源；若Product Design已明确筛选方式，必须写明“沿用Product Design的筛选方式”；若为平铺筛选，在筛选区组件说明中统一列出各独立组件名称，筛选字段表格写清选项范围、默认值和匹配方式；若为高级搜索框，写清每个字段的筛选方式，例如单选、多选、模糊搜索、精确搜索或时间范围筛选；如果页面需要生成HTML说明书，左侧目录只用于锚点定位，不控制页面内容加载或隐藏，该要求属于HTML生成规范，不属于产品Coding实现规范>
- 分页与排序：<说明是否分页、默认排序字段、可排序字段和排序后页面反馈>
- 状态与边界说明：<说明空状态、搜索无结果、加载态、异常态、无权限态、长文本、0值、空字段等在该表格区如何展示>

### 示例：表单区

先说明表单区在页面中的相对位置、承载目标和字段分组，再按以下格式逐项描述字段。表单类区块必须说明每个字段对应的组件，不能只列字段名称。

| 字段名称 | 组件类型 | iDux组件名称 | 必填 | 默认值 | 选项/规则 | 提示信息或联动关系 |
| -------- | -------- | ------------ | ---- | ------ | --------- | ------------------ |
| <字段1> | 输入框/文本域 | <组件名：匹配 Product Design 已登记业务封装时以其为准，否则以 Common Design 组件映射表为准> | 是/否 | <默认值> | <长度、格式或校验规则> | <占位提示、错误提示、提交失败反馈或说明文案> |
| <字段2> | 单选框/复选框/下拉单选/下拉多选 | <组件名：匹配 Product Design 已登记业务封装时以其为准，否则以 Common Design 组件映射表为准> | 是/否 | <默认选项> | <具体选项；如支持下拉搜索，说明可搜索对象和匹配方式> | <选中后是否出现子配置项、影响其他字段或改变可选范围> |
| <字段3> | 开关/日期选择器/数字输入框/人员选择器/单选卡片 | <组件名：匹配 Product Design 已登记业务封装时以其为准，否则以 Common Design 组件映射表为准> | 是/否 | <默认值> | <取值范围、候选来源、状态值或可选值> | <联动关系、子配置面板、禁用条件或辅助说明> |

### 字段形态键对照（RULE-41）

不同字段形态在HTML生成器中渲染的键固定，字段内容必须写在对应形态实际渲染的键上，禁止跨形态套键；键写错会导致HTML对应列静默空白，生成前由校验器RULE-41阻断（error），内容已渲染但键写错位置时提示修正（warning）。

| 字段形态 | JSON数组 | 渲染键（内容写这里） | 禁止使用（写了不会被渲染） |
| -------- | -------- | -------------------- | -------------------------- |
| 表单字段 | `formFields` | `rules`（选项/规则）、`tips`（提示信息或联动关系） | `options`、`description` |
| 筛选字段 | `filterFields` | `options`（选项范围）、`description`（说明） | `rules`、`tips` |
| 表格字段 | `tableFields`/`columns` | `display`（展示形式）、`description`（说明） | `rules`、`tips`、`options` |

表单字段对象示例（正确键名，对应上表“选项/规则”与“提示信息或联动关系”两列）：

```json
{"name": "策略名称", "iduxComponent": "IxInput", "required": "是", "default": "-", "rules": "必填；长度不超过64字符\n仅支持中文、英文、数字与下划线", "tips": "名称在同终端组内唯一"}
{"name": "生效范围", "iduxComponent": "IxSelect", "required": "是", "default": "全部终端", "rules": "选项：全部终端\n指定终端组\n支持按名称搜索终端组", "tips": "选择指定终端组时联动展示终端组多选"}
```

预览视图中表格宽度已锁定为卡片容器宽度，单元格已开启任意字符断行（overflow-wrap:anywhere）与换行符保留（white-space:pre-line），长选项、长校验规则或长提示会按列宽自动折行，不再撑破卡片容器。多条内容必须分行书写：`rules`/`tips` 内有多条选项、规则或提示时，用换行符（JSON字符串中的`\n`）分隔，每条单独一行，预览时逐行展示；禁止在内容中书写`<br>`等HTML标签（会被转义为纯文本原样显示）。

表单字段中表示“选项/枚举/校验规则”的内容必须写入`rules`，表示“提示、错误反馈、联动关系”的内容必须写入`tips`；把内容写成`options`/`description`会造成HTML这两列空白且此前不报错，正是RULE-41要拦截的静默丢失。区块级自由文本`fields`数组中的字典字段按区块标题推定形态（含“表单”按表单键、含“表格/列表”按表格键），同样受RULE-41约束。

## 底部操作

如果有底部按钮，说明按钮文案、用途和点击反馈；提交类按钮需要说明校验规则、提交中状态、成功反馈、失败反馈和数据变化；取消或关闭按钮需要说明是否触发未保存离开确认。如果没有底部按钮，可以不输出本小节。

## 页面级AI Coding指导

<页面级AI Coding指导开头必须先输出该页面的模板契约（templateId、navigationType、templateSource、模板必需区域、区域顺序、底部操作契约），作为AI Coding必须继承的模板结构硬约束；随后以开发项为单位输出，使用“编号、开发对象、开发方式、复用与代码映射、实现要求、完成判定”六列表格；开发项必须使用固定JSON结构（id/scope/name/mode/mappingRef/mappingStatus/target/requirements/acceptanceCriteria等），页面codingGuide固定为pageContext+implementationRules+items+mockContract+stateContract+acceptanceCriteria+outOfScope，详细字段规范见Coding指导与执行规范。若该页面有单独实现要求，写组件、Mock数据、状态更新和复用代码建议。总结性AI Coding指导放在HTML总览页。页面级AI Coding指导必须引用页面内容区块说明中的交互、状态值、筛选范围和表单选项，不另起一套规则。>

如果页面内容区块中简要使用了Product Design或已有代码中的功能点实现，需要在页面级AI Coding指导中补充关联说明，说明命中的设计依据、在当前页面中的使用位置、复用对象、开发方式和编码注意点。页面级AI Coding指导优先从Product Design、业务设计文档或业务相关输入中查找页面、菜单模块、公共组件和功能链路的映射关系，再决定复用对象与开发方式。不要把业务设计文档全文复制进页面内容区；页面内容区只写必要入口、触发效果和展示/校验规则，详细编码指引放在页面级AI Coding指导中。
```

## 9. HTML说明书结构

HTML说明书标题必须是“XX需求设计说明书”。HTML采用“Markdown源文 + 预览视图”双模式：Markdown源文包含完整设计说明书，所有总览和页面内容默认全部展开；左侧目录只负责锚点定位，不做点击后才加载页面，不隐藏页面主体内容。页面提供“源文/预览”切换按钮，预览视图仅用于人类审阅。

左侧目录只包含：总览和页面目录。禁止在HTML目录中放待确认问题、独立的交互与逻辑规则页或独立的Coding指导页。

页面目录必须按页面层级结构展示，而不是扁平罗列；页面名称必须带页面ID，格式为`页面ID-页面名称`。例如：

```text
- 总览
- P001-防火墙策略管理
  - P002-新增防火墙策略
- P003-防火墙规则组
  - P004-新增防火墙规则组
    - P005-新增防火墙规则
```

右侧内容规则：

- 点击“总览”：展示需求概括、导航结构、页面总览表和总览AI Coding指导。
- 点击具体页面：以一列结构展示页面目标、页面基础信息、页面内容区块、底部操作和页面级AI Coding指导；页面类型不要作为标题旁标签展示，必须与页面布局放在同一个“页面基础信息”区域，导航位置必须在页面基础信息中用“一级导航、二级导航、三级导航、Tab页面”表格展示。
- 交互与逻辑规则必须整合到对应页面的内容区块说明中：属于P001的搜索筛选、排序分页、状态值、空状态和列表操作写在P001的表格区或概览区说明中；属于新增弹窗的表单校验、下拉选项、提交反馈和二次确认写在新增弹窗的表单区或底部操作说明中。禁止在页面内再单独生成“页面内关键交互”或“页面交互与逻辑规则”章节。
- Coding指导按层级放置：总览AI Coding指导写全局复用策略、全局Mock数据、全局编码约束和页面开发顺序；页面级AI Coding指导开头输出模板契约（templateId/templateSource/模板必需区域/区域顺序/底部操作契约），随后写单个页面的开发项编码指导表、页面级Mock数据要求和页面级补充说明。

## 10. 自检规则

- 对话框主体是否只输出到页面总览表，之后只给待确认问题、HTML文件路径和简短说明。
- Demo范围是否过滤掉线下流程、外部系统、技术实现和商业背景。
- 用户提到已有模块、参考模块或当前存在Demo代码环境时，是否读取相关代码作为页面拆解、交互说明和Coding指导输入。
- 待确认问题是否控制在10个以内，且每个问题包含影响范围和当前默认假设。
- 页面总览表中的页面ID、页面名称、页面类型（Common Design 中文名）和HTML逐页说明是否一致。
- 页面集合是否为 Step 4 已确认的冻结基准清单的逐项展开（`overview.pageOverview` 与基准原样一致、`pages` 与之一一对应），是否存在对话框已确认但说明书被遗漏或弱化的页面/功能。
- HTML中每个页面是否包含页面区块、字段展示、按钮、可点击操作和点击结果。
- HTML中搜索、筛选、重置、分页、排序是否已整合到对应页面的表格区、工具栏或相关内容区块说明中。
- HTML中新增、编辑、删除、处置、启用、禁用等操作是否已整合到对应页面的区块说明或底部操作中，并写清校验、反馈和状态变化。
- HTML中高影响操作是否有二次确认。
- HTML中空状态、加载态、异常态、无权限态和极端数据是否覆盖。
- HTML中Mock数据是否覆盖主要状态和边界情况。
- HTML说明书是否包含标题、左侧目录、总览页和按页面层级组织的逐页内容；是否没有把待确认问题、全局交互规则页或独立Coding指导页放入HTML目录。
- 代码可用状态是否标记并写入 Design Context；`partial` / `unavailable` 状态下是否未虚构真实代码对象，语义级对象是否标记“Coding 阶段待核验”。
- 属于已有业务主题或页面体系时，是否已把真实参考页面作为视觉基线并写入 Design Context 和页面总览。
- 每个页面是否已绑定标准 templateId（或 custom 模板且含 baseTemplateId、customReason、overrideSource、overrideJustification），并填写 templateContract；是否使用了未注册页面类型名称；页面 type、templateId、layout、sections、wireframe、footerActions、componentContract、codingGuide 是否形成闭环；页面 templateContract 是否登记 `templateBase`（common/product）与 `productTemplateRef`（`templateBase=product` 时非空且可定位到 Product Design 模板文档原文），页面模板来源判定是否在 HTML 生成前完成并依据原文。
- 结构化 wireframe 是否作为唯一可信来源（templateId/navigationType/shell/regions/variants 完整）；多步骤或 Tab 页面是否包含主结构图和每个步骤/Tab 一张完整变体图，变体是否保留公共页面外壳；footerActions 对齐与按钮顺序是否与模板契约一致或已有 override 记录；wireframe.ascii 底部操作区是否已按模板 buttonOrder 绘制模板按钮（不得只画关闭或漏画主操作），底部自定义按钮是否已声明 override；`regions[].position` 相对顺序是否与 wireframe.ascii 区域首次绘制行序一致、页面级单例控件与内容区域是否未重复绘制、内容行右边界是否对齐；`templateContract.override.enabled=true` 时是否已放宽必需区域/区域顺序/必需组件/表格语义断言并在 `override.source` 登记覆盖来源；纯字符串 wireframe 是否已进入 legacy 警告。
- 表单/筛选中带固定选项的下拉类字段，是否在选项单元格逐项完整列出全部选项、未使用“等/例如/…”只举例；页面是否以 `requirementOptionSets` 声明固定选项字段的完整选项集并被 RULE-48 校验（缺失阻断、截断指纹告警）；需求源枚举表含分组/层级列时是否保留该维度（声明 `dimension=group/hierarchy` 或 `sourceColumns` ≥2 列），选项单元格未被压成单层列表（压平以 OPTION_DIMENSION_LOST 告警），且承载该维度的控件形态已按 RULE-54 依 widget patterns 判定并登记依据。
- 详情页是否已确认顶部概览卡片/对象摘要字段与下方详情描述列表不重复（概览卡片已展示字段不再进描述列表）；是否以 `detailSummaryFields` 声明概览字段、必要时用 `detailDedupExempt` 说明有意重复（RULE-49）。
- 详情页是否已确认顶部概览卡片/对象摘要的**操作按钮**（编辑/重启/删除等对象级操作）未在底部按钮栏（`footerActions`）重复出现（概览卡片承载对象级操作、底部按钮栏只保留关闭/上一个/下一个/取消/确定）；必要时以 `detailActionDedupExempt` 说明有意重复（RULE-58）。
- 按钮/可点击操作是否已改为表格（操作/触发方式/使用组件/文案或字段/Demo反馈/来源）？高影响操作（可配置+自动识别）是否写明确认文案（缺失阻断）；涉及二次确认或局部面板的操作是否写清组件与文案/字段；组件与文案来源是否优先取自 Product Design（其次 Common Design）的 pattern 并登记锚点、未由 AI 自拟（RULE-50）。
- 线框图中表格关联按钮（批量操作、子功能入口等）是否统一绘制在表格区左上角工具栏，未出现在表格框下方或工具栏之外的区域（RULE-51）。
- PRD 点名的每个入口挂载点是否已在 `requirementEntryPoints` 逐条声明；in-scope 入口是否落到宿主页面区块操作或 `operations` 并绘入宿主线框图；out-of-scope 宿主是否已在 `entryHosts` 登记（含 Tier1 精读、宿主线框图、开发项）；宿主为既有页面时是否已建立其既有形态视觉基线（RULE-52）。
- 定位到既有页面（入口宿主、复用/相似页面）时是否登记了可核验的身份证据（逐级导航路径 + 路由/菜单标识 + 标题 + 命中代码实体 + 命中依据）；是否未以文件名/目录名作为定位依据；是否对形近候选逐条排除、是否与 PRD 声明路径对证末级语义（RULE-53）。
- 多形态组件（在已读取的 Common Design 组件映射中登记了多种形态，如 IxTag 多种标签样式、IxSelect 下拉面板的搜索/新增/树/分组、单选/多选的 radio/卡片）是否在 `iduxComponentForm` 写明本页选用的形态，且 `formCandidates` 取自组件映射的登记形态；形态的**选择依据**是否已按命中的 `03-patterns/07-widget-patterns/` 判定小节读取并锚点级登记（`designReferences` + `readLedger` 命中 `status=read`）；声明了 `formCandidates`（>1）却未选形态、所选形态不在候选内、缺组件映射依据、缺 widget pattern 选择依据（或依据未精读命中）会被 RULE-54 告警（warning）。
- 表单承载页（配置表单页、下钻步骤条配置页、表单弹窗、表单抽屉，或含表单配置区块的页面）的线框是否**单列**——每行一个配置项、label 在左控件在右且水平同一行，未把两个及以上配置项画在同一行（含 variants 图）；表单布局依据（Common Design 表单规范）是否已锚点级登记并精读；一行多配置项以 FORM_LAYOUT_MULTI_COLUMN 告警、label 与控件不同行以 FORM_LAYOUT_LABEL_NOT_INLINE 告警、依据未登记或未精读以 FORM_LAYOUT_BASIS_UNREAD 告警（RULE-57，均 warning）。
- 需求延伸容器（按钮点击/表格字段点击/详情字段点击/行操作/导入导出触发的弹窗、抽屉、子页面）若命中 Product Design 业务封装组件或代码已知业务封装功能，是否**未单独描述该容器**：不画线框图、不写页面内容区块与底部操作，只在宿主页面写明"点击 X 打开 Y（复用 <组件名>，不单独绘制）"，并把复用组件登记为开发项与依据；未按此降级而自绘的会以 REUSE_CONTAINER_OVER_DESCRIBED 阻断（RULE-59，其余为 warning）；需求直接点名的页面不受此口径影响，必须完整产出。

## 11. 设计闭环自动校验

设计闭环用于防止已确认的页面、容器、操作、需求入口与 Tab 在设计说明书生成过程中丢失，并在 HTML 生成前阻断结构不完整的说明书。校验由 `scripts/validate_demo_spec.py` 执行（RULE-28 ~ RULE-59，含字段完整性 RULE-36、表格详情字段一致性 RULE-38、表格标签使用约束 RULE-39、设计依据一致性 RULE-43、未核验实现细节隔离 RULE-44、下拉选项完整性 RULE-48、详情页字段去重 RULE-49、按钮/可点击操作表 RULE-50、表格区按钮位置 RULE-51、需求入口落位闭环 RULE-52、页面定位证据闭环 RULE-53、组件形态描述 RULE-54、能力发现完整性 RULE-55、模板 ID 一致性与覆盖兜底 RULE-56、表单单列布局闭环 RULE-57、详情页操作去重 RULE-58 与复用业务组件容器闭环 RULE-59），生成器 `scripts/generate_demo_spec_html.py` 在 strict 模式下遇到 error 即阻断生成。

### 11.1 页面清单闭环（RULE-28）

- `overview.pageOverview` 是已确认页面/容器清单（manifest），每项可声明 `containerType`（page/modal/drawer）。
- 页面对象必须位于 `pages` 顶层，每个页面、弹窗、抽屉都是 `pages` 数组的独立元素；`children` 仅用于表达归属关系，只允许写子容器 ID（字符串），禁止在 `children` 中内嵌完整页面设计对象（内嵌对象会被 RULE-35 阻断）；校验展开全部 `pages` 元素与 `pageOverview` 对比。
- 页面对象可通过 `containerType` 显式声明容器类型；未声明时按 templateId 推断（含 `modal` 为弹窗、含 `drawer` 为抽屉、其余为页面）。
- 校验项（error 阻断 / warning 提示）：
  - 已确认页面/容器在 pages 缺失 -> MANIFEST_PAGE_MISSING（error）
  - pages 存在总览未列出的页面 -> MANIFEST_EXTRA_PAGE（error）
  - 页面总览 ID 重复 -> MANIFEST_DUPLICATE（error）
  - 同 ID 的 name / type / containerType 不一致 -> MANIFEST_METADATA_MISMATCH（error）
  - 弹窗/抽屉容器没有任何入口（无 open-container 操作引用且无文本引用）-> ORPHAN_CONTAINER（已确认容器 error，未确认容器 warning）
  - 需求/规范明确列出的字段（requirementFieldNames）未落入对应区块字段数组（tableFields/formFields/filterFields/cardFields 等）且无 excludedFields 排除原因 -> REQUIRED_FIELD_MISSING（error，RULE-36）
  - 固定选项型下拉声明的完整选项（requirementOptionSets）未全部落入表单 `rules` 或筛选 `options` 单元格 -> REQUIRED_OPTION_MISSING（error）；声明字段不存在 -> OPTION_FIELD_NOT_FOUND（error）；未声明选项集的选择类字段选项单元格出现 等/例如/如：/… 截断指纹 -> OPTION_TRUNCATION_MARKER（warning，RULE-48）；需求源枚举表含分组/层级列（声明 `dimension=group/hierarchy` 或 `sourceColumns` ≥2 列）但选项单元格被压成单层列表、未保留该维度 -> OPTION_DIMENSION_LOST（warning，RULE-48）
  - 详情类页面中，概览卡片/对象摘要已展示字段（detailSummaryFields 声明，或 cardFields/摘要型区块启发式）又在详情描述列表重复出现 -> DETAIL_FIELD_DUPLICATE（warning）；同一详情描述列表内字段名重复 -> DETAIL_FIELD_DUPLICATED_IN_LIST（error，RULE-49）
  - 页面含概览卡片/对象摘要区块且该区块声明 `actions` 时：概览卡片已承载的对象级操作（编辑/重启/删除等）又出现在底部按钮栏 `footerActions` -> DETAIL_SUMMARY_ACTION_DUPLICATE（warning，RULE-58；按操作名同义归一比较，`detailActionDedupExempt`/`excludedActions` 豁免）
  - 声明复用业务组件的需求延伸容器（`reuseBusinessComponent.decision=reuse`）仍自绘线框/区块字段/底部操作 -> REUSE_CONTAINER_OVER_DESCRIBED（**error**，RULE-59）；复用依据未锚点级登记或未精读命中、`basis=code` 缺 `codeEvidence` -> REUSE_BASIS_UNREAD（warning）；宿主页面未交代复用 -> REUSE_HOST_NOTE_MISSING（warning）；`trigger` 非法 / `hostPageId` 缺失或不在范围 / 容器无宿主入口 -> REUSE_SCOPE_INVALID（warning）；容器已有宿主入口且已引用 Product Design 业务组件依据却未声明复用 -> REUSE_CANDIDATE_UNMARKED（warning）
  - 高影响操作缺二次确认文案 -> ACTION_CONFIRM_TEXT_MISSING（error）；涉及二次确认/局部面板但缺组件、或声明组件却无文案/字段 -> ACTION_COMPONENT_MISSING / ACTION_CONTENT_MISSING（warning）；组件/文案来源缺失、标为 ai-fill、缺锚点或取值非法 -> ACTION_SOURCE_NOT_TRACED（warning）；操作行缺名称 -> ACTION_NAME_MISSING（warning，RULE-50）
  - 线框图中表格关联按钮（批量操作/子功能入口等）绘制在表格框下方 -> TABLE_BUTTON_MISPLACED（warning）；批量操作按钮未置于表格区左上角工具栏 -> TABLE_ACTION_NOT_IN_TOOLBAR（warning，RULE-51）
  - 表单承载页（配置表单页/下钻步骤条配置页/表单弹窗/表单抽屉，或含表单配置区块）线框 ascii（含 variants）同一行出现 >=2 个已声明表单字段 -> FORM_LAYOUT_MULTI_COLUMN（warning）；字段名与控件不在同一行（label 独占一行、控件在下一行）-> FORM_LAYOUT_LABEL_NOT_INLINE（warning）；表单布局依据（Common Design 表单规范）未锚点级登记或未在 readLedger 命中 status=read -> FORM_LAYOUT_BASIS_UNREAD（warning，RULE-57）
  - coverage/capabilitySweep 声明 appliesTo 却未命中任何页面 -> TEMPLATE_COVERAGE_UNAPPLIED（warning）；templateSource/layoutSource/组件来源引用已废弃旧模板 ID -> LEGACY_TEMPLATE_ID_REF（warning，RULE-56）

```json
"overview": {
  "pageOverview": [
    {"id": "P01", "name": "策略列表", "type": "基础表格页", "containerType": "page"}
  ]
}
```

### 11.2 操作目标闭环（RULE-29）

- 页面级 `operations` 数组声明结构化操作，`action` 区分：`open-container`、`confirm`、`download`、`refresh`、`delete`、`batch-delete`、`disable`、`enable`、`revoke`、`submit`、`navigate`、`close`、`other`。
- `open-container` 必须声明 `targetPageId` 与 `targetContainerType`；目标页面必须存在且容器类型匹配。
- `delete` / `batch-delete` / `disable` / `enable` / `revoke` 等高风险操作必须 `confirm: true` 并附 `confirmConfig`。
- 校验项（error 阻断 / warning 提示 / info 说明）：
  - open-container 缺 targetPageId 或目标页面不存在 -> OPERATION_TARGET_MISSING（error）
  - targetContainerType 与目标页面实际容器类型不一致 -> OPERATION_CONTAINER_TYPE_MISMATCH（error）
  - 高风险操作缺少二次确认 -> OPERATION_CONFIRM_MISSING（error）
  - 未知 action -> OPERATION_ACTION_UNKNOWN（warning）
  - action 为 other -> OPERATION_ACTION_OTHER（info，需人工核验）

```json
"operations": [
  {"id": "OP01", "action": "open-container", "label": "批量编辑主机资产", "trigger": "工具栏按钮",
   "targetPageId": "P02", "targetContainerType": "modal", "confirm": false},
  {"id": "OP02", "action": "delete", "label": "删除", "trigger": "行内操作", "confirm": true,
   "confirmConfig": {"title": "确认删除该策略？", "level": "danger"}}
]
```

### 11.3 Tab 变体闭环（RULE-30，条件式）

- 仅当页面显式声明 `tabs` 且数量 >= 2 时强制 Tab 变体闭环；单内容 Tab 页面或普通详情页仍可使用单张 wireframe。
- 页面级 `tabs` 数组：每项 `tabId` 唯一、`name` 为 Tab 名。
- `wireframe.variants` 每项通过 `tabId` 关联 Tab；数量必须与 tabs 一致，每个 Tab 有对应 variant，不允许孤立 variant。
- 每个 variant 必须保留公共页面外壳（preserveRegions 包含 title-bar / drawer-shell / modal-shell / object-summary / tab-bar / footer 等外壳区域），并有非空 `changedRegions` 与足够长度的 ascii 线框图，禁止只有空壳或简单文本。
- sections 通过 `tabId` 绑定所属 Tab，保证 sections、tabs、variants、wireframe.regions 可互相追踪。
- 校验项（error 阻断 / warning 提示）：
  - tabId 缺失 -> TABS_ID_MISSING（error）
  - tabId 重复 -> TABS_ID_DUPLICATE（error）
  - variants 数量与 tabs 不一致 -> TABS_VARIANT_COUNT_MISMATCH（error）
  - Tab 无对应 variant -> TABS_VARIANT_MISSING（error）
  - variant.tabId 不存在于 tabs -> TABS_ORPHAN_VARIANT（error）
  - variant 缺少公共页面外壳 -> TABS_VARIANT_NO_SHELL（error）
  - variant 缺少当前 Tab 内容区 -> TABS_VARIANT_NO_CONTENT（error）
  - section 绑定不存在的 tabId -> TABS_SECTION_INVALID（error）
  - 多 Tab 页面 section 未绑定 tabId -> TABS_SECTION_UNBOUND（warning）

```json
"tabs": [
  {"tabId": "tab-overview", "name": "概览"},
  {"tabId": "tab-source", "name": "来源与识别依据"}
],
"wireframe": {
  "templateId": "detail-drawer",
  "variants": [
    {"tabId": "tab-overview", "preserveRegions": ["title-bar", "object-summary", "tab-bar", "footer"],
     "changedRegions": ["tab-content"], "ascii": "┌────────────────────────────┐\n│ 标题栏：对象详情     [关闭] │\n├────────────────────────────┤\n│ 对象摘要：对象A 关键属性    │\n├────────────────────────────┤\n│ Tab行：概览 | 来源          │\n├────────────────────────────┤\n│ 概览内容：                  │\n│ 字段1  值1                 │\n│ 字段2  值2                 │\n├────────────────────────────┤\n│                [关闭]│\n└────────────────────────────┘"},
    {"tabId": "tab-source", "preserveRegions": ["title-bar", "object-summary", "tab-bar", "footer"],
     "changedRegions": ["tab-content"], "ascii": "┌────────────────────────────┐\n│ 标题栏：对象详情     [关闭] │\n├────────────────────────────┤\n│ 对象摘要：对象A 关键属性    │\n├────────────────────────────┤\n│ Tab行：概览 | 来源          │\n├────────────────────────────┤\n│ 来源内容：                  │\n│ 来源类型  自动识别          │\n├────────────────────────────┤\n│                [关闭]│\n└────────────────────────────┘"}
  ]
},
"sections": [
  {"title": "概览", "type": "overview", "tabId": "tab-overview", "description": "对象概览指标"},
  {"title": "来源与识别依据", "type": "descriptions", "tabId": "tab-source", "description": "识别依据描述列表"}
]
```

### 11.4 页面级 Coding 闭环（RULE-31）

- 每个页面的 `codingGuide.pageContext.pageId` 必须等于页面 ID。
- 每个页面 `codingGuide.pageItems` 至少包含 1 个稳定 Coding item；item 若声明 `pageId` 必须等于所属页面 ID；item ID 在页面内唯一。
- 校验项（error 阻断）：
  - pageContext.pageId 与页面 ID 不一致 -> CODING_PAGE_CONTEXT_MISMATCH
  - 页面无任何 Coding item -> CODING_NO_ITEMS
  - Coding item ID 重复 -> CODING_ITEM_DUPLICATE
  - item.pageId 与所属页面不一致 -> CODING_ITEM_ORPHAN

```json
"codingGuide": {
  "pageContext": {"pageId": "P01", "summary": "策略列表页 Coding 上下文"},
  "pageItems": [
    {"id": "P01-C01", "scope": "table-page", "name": "策略列表", "mode": "reuse-framework",
     "mappingRef": "M01", "mappingStatus": "verified",
     "target": {"path": "src/pages/policy/list.vue", "export": "PolicyList"},
     "requirements": ["保留表格工具栏、表格、分页结构"]}
  ]
}
```

### 11.5 错误码与严重级别

- error：设计闭环缺失，禁止生成 HTML（strict 模式阻断）。
- warning：设计质量风险，不阻断 HTML 生成。
- info：AI 补齐或待核验说明，仅提示。

### 11.6 线框图绘制质量闭环

防止"线框图没有画、只有几个字"或"完全没有按照页面模板绘制"的问题。校验器验证的是结构化 regions，同时必须验证实际绘制的 `ascii` 图：

- `ascii` 必须按模板绘制，禁止用一句话或几个字代替线框图。
- 绘制完整性（error）：
  - ascii 内容过短（< 8 字符）-> WIREFRAME_ASCII_TOO_SHORT
  - ascii 未覆盖模板必需区域（匹配到的区域绘制关键词少于 2 个）-> WIREFRAME_ASCII_NOT_DRAWN
  - ascii 是区域标签罗列（每行一个"区域名：内容"、无右竖线闭合、大量分隔线）-> WIREFRAME_ASCII_LABEL_LIST（分隔线判定兼容 `+---+` 与 box-drawing `┌─┐` / `├─┤` / `└─┘` 两种字符画风格）
- 绘制与 regions 一致性（warning）：
  - regions 声明了内容性区域（筛选、表格、分页、工具栏、表单、概览、步骤、对象摘要、Tab 内容、底部操作等），但 ascii 中没有任何对应绘制痕迹 -> WIREFRAME_REGION_NOT_DRAWN
- 绘制区域关键词（REGION_ASCII_KEYS）与模板区域对应：标题栏/筛选/工具栏/表格/分页/表单/弹窗/抽屉/摘要/步骤/Tab/底部操作等；纯结构区域（global-navigation、modal-shell、drawer-shell、title-bar）不参与该一致性检查。校验按行/邻域判定：结构化 ascii 中区域关键词须出现在含框线字符（`│`/`|`/`─`/`┌` 等）的行上，纯字符串 ascii 退化为按分隔符分段匹配，避免整段文本顺带提及即算"已绘制"。
- HTML 生成时若 ascii 过短或无区域绘制痕迹，线框区块渲染提示，提醒检查。
- 线框图样式来源：模板结构与线框样式一律以运行时可读取的 Common Design 页面模板文档（如 02-template/01-page-types.md）为准，本 Skill 不保存页面模板线框图参考。
- 入口挂载点绘制约定：当顶层声明 `requirementEntryPoints` 时，in-scope 入口必须在宿主页面线框图中绘制触发元素（按钮/行内操作）与打开容器关系；out-of-scope 宿主必须在说明书中绘制宿主页面结构并以显式标记高亮入口位置（如 `【xx入口】`），同时画出点击后打开的容器关系。只画入口自己的容器（弹窗/抽屉）而不画宿主结构，视为未绘制（RULE-52 `ENTRY_NOT_DRAWN`）。

数据示例（合法完整线框图）：
```text
┌──────────────────────────────┐
│ 标题栏：事件分析   [导出][刷新]│
├──────────────────────────────┤
│ [筛选] 风险等级 时间范围 [查询]│
│ ┌──────────────────────────┐ │
│ │ 事件名称 | 风险等级 | 操作 │ │
│ │ 事件A    | 高       | 详情 │ │
│ └──────────────────────────┘ │
│ 上一页 1 2 3 下一页            │
└──────────────────────────────┘
```

### 11.7 表格与详情字段一致性闭环（RULE-38）

表格展示部分字段、详情展示完整字段时，表格字段与详情字段必须保持一致：表格页 `tableFields` 中展示的每个字段，都必须在对应详情容器页的字段数组（`detailFields`/`cardFields`/`fields`/`tableFields` 等）中存在对应项，防止"表格有、详情没有"或表格与详情字段对不上的情况。Common Design 已明确"表格展示的字段与详情抽屉字段保持一致"规则，本校验作为自动兜底。

- 详情容器识别：表格页 `operations` 中 `action=open-container` 且目标为详情类容器（页面 type 含"详情"，或 `templateContract.templateId` 含 `detail`，如 `detail-drawer`/`log-detail-drawer`/`page-detail-drilldown`），以及 `children` 挂载的详情容器；表格页无详情容器时不校验（非"表格有详情"场景）。
- 字段匹配：字段名去除空格/下划线/括号等符号后精确匹配，或一方包含另一方（双方长度 >= 2）视为对应。
- 校验项（error 阻断）：
  - 表格展示的字段在关联详情容器中不存在 -> TABLE_DETAIL_FIELD_MISMATCH（error，RULE-38）

```json
"operations": [
  {"id": "OP01", "action": "open-container", "label": "查看详情", "trigger": "行内操作",
   "targetPageId": "D01", "targetContainerType": "drawer", "confirm": false}
]
```

表格页 `tableFields` 中展示的每个字段必须能在 D01 的 `detailFields`/`cardFields`/`fields`/`tableFields` 中找到对应；缺失时阻断 HTML 生成。

### 11.8 表格标签使用约束闭环（RULE-39）

Common Design 已明确标签（IxTag）样式使用约束：同一个表格内标签使用数量受限、样式需克制，配额优先留给需要凸显的重要业务状态。本校验作为自动兜底（双重检查），按"表格区块"（sections 中带 `tableFields` 的区块 + 页面级 `tableFields`）逐块统计：

- 标签字段识别：字段 `iduxComponent` 为 `IxTag`（含 `IxBadge/IxTag` 等组合，排除选择类组件），或 `component`/`display` 含"标签"（如"单标签/多标签"）。
- 标签样式识别：从字段 `display`/`description`/`style`/`tagType`/`tagStyle` 文本中匹配样式关键词——"深色/dark"为深色标签、"icon/图标/带图标"为 icon 标签、"点状/状态点/dot"为点状标签、"浅色/light"为浅色标签。
- 校验项（error 阻断）：
  - 同一表格内标签使用数量 > 5 -> TABLE_TAG_COUNT_EXCEEDED（error，RULE-39）
  - 深色/icon/点状标签各自出现次数 > 1 -> TABLE_TAG_STYLE_OVERUSED（error，RULE-39）
  - 浅色标签出现次数 > 2 -> TABLE_TAG_STYLE_OVERUSED（error，RULE-39）
- 校验项（warning 提示，双重检查盲区与配额优先级）：
  - 同一表格内存在 >= 2 个标签字段且样式未标注 -> TABLE_TAG_STYLE_UNSPECIFIED（warning，RULE-39），提示补充样式标注以便自动校验"同一样式仅允许 1 次"
  - 中性描述字段（如资产类型、IP、域名、端口、路径、地址、主机、编号等）使用标签组件 -> TABLE_TAG_NEUTRAL_FIELD（warning，RULE-39），提示标签配额优先留给风险等级、处置状态/启用禁用状态、本身命名为"标签"的字段，中性字段改用普通文本或等宽文本

```json
"tableFields": [
  {"name": "风险等级", "display": "深色标签", "iduxComponent": "IxTag", "description": "高/中/低"},
  {"name": "处置状态", "display": "状态点+文字", "iduxComponent": "IxBadge/IxTag", "description": "待处置/处理中/已处置"}
]
```

同一表格内深色标签仅 1 个、点状标签仅 1 个，未超过配额；若再增加深色或点状标签字段，会被 RULE-39 阻断。

### 11.9 需求理解与页面设计追溯（RULE-42）

生成 HTML 前，页面设计与需求理解模型必须双向可追溯，防止只按需求字面翻译、页面与用户要完成的业务任务脱节。追溯要求：

- 每个页面必须关联至少一个业务任务：页面对象写入 `taskRefs`（引用 `requirementUnderstanding.tasks` 的任务 id），并写明 `businessObject`（承载的业务对象）与 `pageDecisionPurpose`（该页面帮助用户完成什么决策/任务）。
- 每个核心业务任务必须有页面承载：`requirementUnderstanding.tasks` 中的任务 id 必须至少被一个页面的 `taskRefs` 引用；任务应具备完整定义（角色、触发、对象、动作、判断信息、结果、状态、异常），缺少核心动作会被拦截。
- 每个核心动作必须有结果反馈：任务定义了 `action` 但未定义 `outcome`（成功/失败/部分成功及状态变化）时，页面无法表达结果，会被拦截。
- 页面区块必须说明服务哪个判断点：区块写入 `informationPurpose`（支撑哪项判断）与 `decisionPoint`（触发哪个动作分支/决策），用于验证信息层级服务于用户任务。
- 关键字段必须说明用途：字段字典写入 `fieldRole`，取值 `identify`（识别信息）/ `judge`（判断信息）/ `precondition`（操作前置）/ `result`（结果反馈）；声明了判断点的区块内字段缺少 `fieldRole` 给 warning。
- AI 推导字段必须标记来源：AI 补齐的字段、区块或内容写入 `source: "ai-fill"`，合法来源标记为 `requirement` / `product-design` / `common-design` / `code` / `ai-fill`；显式声明的来源值非法给 warning。
- 未解决的业务事实不得写入 HTML 作为确定设计：`requirementUnderstanding.status` 必须为 `resolved`，`needs_confirmation` / `blocked` / 缺失时阻断 HTML 生成，先完成 SKILL.md Step 1.5 的确认（见 07-requirement-understanding.md）。

自动校验 RULE-42（条件式启用：顶层声明 `requirementUnderstanding` 或任一页面带 `taskRefs` 时触发；历史未建模格式不误伤）：

| 场景 | 级别 | errorCode |
|---|---|---|
| 页面带 `taskRefs` 但顶层缺少 `requirementUnderstanding` 模型 | error | REQ_TRACE_MODEL_MISSING |
| `requirementUnderstanding.status` 缺失或非 `resolved`（未解决的业务事实写入 HTML） | error | REQ_TRACE_STATUS_NOT_RESOLVED |
| 页面没有 `taskRefs` 或为空 | error | REQ_TRACE_NO_TASK_REF |
| 已建模业务任务没有任何页面 `taskRefs` 引用 | error | REQ_TRACE_TASK_UNBOUND |
| 任务缺少核心动作定义 | error | REQ_TRACE_TASK_INCOMPLETE |
| 任务有核心动作但没有结果反馈（`outcome` 为空） | error | REQ_TRACE_ACTION_NO_OUTCOME |
| 声明判断点的区块内字段未说明用途（缺 `fieldRole`） | warning | REQ_TRACE_FIELD_NO_PURPOSE |
| `fieldRole` 显式声明的值非法 | warning | REQ_TRACE_FIELD_ROLE_INVALID |
| `source` 显式声明的值非法 | warning | REQ_TRACE_SOURCE_INVALID |

### 11.10 设计依据一致性（RULE-43）

条件式启用：顶层声明 `designContext` 时触发；历史未声明 `designContext` 的 JSON 不启用（不误伤）。

本闭环用于堵住两类静默缺陷：引用未实际读取的设计文档作为依据，以及 Product Design 声明页面模板覆盖但页面实际落到 Common Design。

结构化载体（顶层 `designContext`）：

路径占位声明：`common-design/...` 路径为 Common Design 的真实路径，可直接引用（页面模板固定在 `references/02-template/`，组件映射固定在 `references/05-components/`，组件形态使用判定固定在 `references/03-patterns/07-widget-patterns/`，目录级读取用 `common-design/references/03-patterns/07-widget-patterns/#*` 留索引痕迹，作为依据时必须精确到命中文件的小节锚点）；`product-design/...` 路径**本 Skill 一律不预置**——Product Design 的目录结构随产品而异，其文档路径与章节锚点必须取自当前实际加载的 Product Design Skill，示例中一律写作 `<product-design 文档路径>#<章节锚点>` 占位。引用路径与真实目录不一致时，`designReferences.ref` 既无法在 `readLedger` 锚点级命中（RULE-43 阻断），也无法供人工直达原文复核。

```json
"designContext": {
  "commonDesign": {"skillId": "common-design", "read": true},
  "productDesign": {
    "matched": true,
    "skillId": "<product-design-skill-id>",
    "coverage": [
      {"capability": "template", "relation": "override", "appliesTo": ["page-table-overview"]},
      {"capability": "filtering", "relation": "override", "appliesTo": ["page-table-overview"]},
      {"capability": "theme", "relation": "extend", "appliesTo": []}
    ],
    "capabilitySweep": [
      {"capability": "template", "decision": "hit", "reason": "覆盖概览页模板", "appliesTo": ["page-table-overview"]},
      {"capability": "filtering", "decision": "hit", "reason": "覆盖筛选区形态", "appliesTo": ["page-table-overview"], "evidenceRef": "<product-design 文档路径>#<章节锚点>"},
      {"capability": "theme", "decision": "not-hit", "reason": "本需求不涉及主题层"}
    ]
  },
  "readLedger": [
    {"ref": "common-design/references/02-template/01-page-types.md#page-table-overview", "status": "read"},
    {"ref": "<product-design 文档路径>#<章节锚点>", "status": "read"},
    {"ref": "<product-design 文档路径>#*", "status": "read"},
    {"ref": "product-design/SKILL.md#*", "status": "index-only"}
  ]
}
```

readLedger 采用**锚点粒度**：每条为 `{ "ref": "<文档路径>#<章节/模板条目>", "status": "read|index-only" }`；整篇已读用 `#*` 显式声明。

| 场景 | 级别 | errorCode |
|---|---|---|
| `designReferences` 中 `common-design` / `product-design` 来源的 `ref` 未在 `readLedger` 中**锚点级**命中（读了同文档的另一小节不算） | error | DESIGN_REF_UNREAD |
| 命中的 `readLedger` 条目状态为 `index-only`（仅读索引/摘要却作为依据） | error | DESIGN_REF_UNREAD |
| 该来源 `ref` 不是精确锚点（缺少 `#`） | warning | DESIGN_REF_UNANCHORED |
| Product Design 声明某能力（含模板）`extend` / `override` 且页面命中，但该页未登记同 `ability` 的 `source=product-design` 依据 | error | ABILITY_SOURCE_NOT_REGISTERED |
| Product Design 声明页面模板 override 且页面命中，但页面 `templateContract.templateBase != product` 或 `productTemplateRef` 为空（应用 Product Design 效果却落到 Common Design） | error | TEMPLATE_OVERRIDE_NOT_APPLIED |
| 页面 `templateBase=product` 但未声明 `productTemplateRef`、或 `designContext` 未声明 `productDesign.matched=true`、或未登记 `source=product-design` 依据 | error | TEMPLATE_SOURCE_UNREGISTERED |
| `productDesign.matched=true` 但缺少 `skillId` | warning | DESIGN_CONTEXT_INCOMPLETE |

匹配规则：`readLedger.ref` 与 `designReferences.ref` 均归一化为 `<文档路径>#<锚点>`；命中要求**文档与锚点同时一致**且 `status=read`；`#*` 表示整篇已读（覆盖该文档任意锚点）。页面命中某能力时，`designReferences` 依据条目用 `ability` 字段标注对应能力。

能力范围不止模板：Product Design 对 `component`（组件映射/业务封装组件）或 `pattern`（交互模式，如筛选方式）等能力声明 `extend` / `override` 且页面命中时，页面必须登记同 `ability` 的 `source=product-design` 依据（否则 `ABILITY_SOURCE_NOT_REGISTERED`），且组件名不得一律退回 Common Design 通用组件；Pattern 层 `component_requirements` 结论须回填到页面 `componentContract.patternComponents`。

### 11.11 未核验实现细节隔离（RULE-44）

设计阶段（`partial` / `unavailable`）只做设计语义，不把未核验的实现细节当作已确认设计结论。`codeAvailability` 缺省时按 `unavailable` 处理（RULE-24 `CODE_STATUS_UNDECLARED` 提示），不再静默跳过。

| 场景 | 级别 | errorCode |
|---|---|---|
| 未声明 `codeAvailability`（按 unavailable 处理） | warning | CODE_STATUS_UNDECLARED |
| `partial` / `unavailable` 下 `codingGuide.pageItems[].target.path` 非空 | error | PATH_WITHOUT_VERIFY |
| `partial` / `unavailable` 下 `target.export`（真实导出名）非空 | error | EXPORT_WITHOUT_VERIFY |
| `partial` / `unavailable` 下字段 / 编码指导 / 复用映射出现未核验的产品专有组件名（非 `Ix` 标准组件） | error | COMPONENT_WITHOUT_VERIFY |
| `partial` / `unavailable` 下 `mappingRef` 为真实文件路径 | error | MAPPINGREF_WITHOUT_VERIFY |
| `partial` / `unavailable` 下 `visualBaselineRef` 指向真实可视化基线页面 | error | VISUAL_BASELINE_WITHOUT_VERIFY |
| `partial` / `unavailable` 下 `restoreRequirement.components[].path` 非空 | error | COMPONENT_PATH_WITHOUT_VERIFY |
| `partial` / `unavailable` 下业务组件名已被 Product Design 登记（`designReferences` 的 `source=product-design` 的 `ability` / `component` / `components`，或 `componentContract.patternComponents[].components`） | warning | COMPONENT_WITHOUT_VERIFY |

组件名判定：令牌以大写字母开头的驼峰 / 缩写名且包含 >= 2 个大写字母、且不以 `Ix` 开头（iDux 标准组件豁免）；字段表（`tableFields` / `formFields` / `filterFields` / `columns` 的 `iduxComponent` / `component`）、编码指导 `target.component` / `target.components`、复用映射 `restoreRequirement.components[].name` 均在扫描范围。

Product Design 已登记降级：当某组件令牌已被页面的 Product Design 依据登记（`codingGuide.designReferences` 中 `source=product-design` 条目的 `ability` / `component` / `components`，或 `componentContract.patternComponents[].components`）时，视为“PD 已登记但代码未核验”，级别由 error 降为 warning（errorCode 仍为 `COMPONENT_WITHOUT_VERIFY`），提示保留业务组件名并标注“待 Coding 阶段核验”，不得因此退回 iDux 通用组件。

设计意图与实现名的位置边界（RULE-44 的允许表达与禁止位置）：

| 位置 | 性质 | 是否允许写未核验的业务组件名 |
|---|---|---|
| `componentContract`（含 `patternComponents`）、`codingGuide.implementationNotes`、`codingGuide.designReferences`（用 `ability` 表达） | 设计意图 | 允许；须以语义级能力名表达并标注“待核验”，来源为 Product Design 时登记 `source=product-design` 与 `ability` |
| 字段级 `iduxComponent` / `component`、`codingGuide.pageItems[].target.component` / `target.components`、`restoreRequirement.components[].name`、`sections[].component` / `filterComponent` / `topComponent` | 实现名 | 禁止写未核验的业务组件真实名；须写 Ix 标准组件或语义级描述，真实导出名留待 Coding Gate |

替代写法：当 Product Design 已登记某业务封装组件、但当前代码状态为 `partial` / `unavailable` 时，不得因为无法核验就一律退回 iDux 通用组件；应在上述“设计意图”位置写“<Product Design 业务能力名>（待 Coding 阶段核验）”，并在 `designReferences` 登记 `source=product-design` + `ability`。

### 11.12 线框与区域结构双向一致性（RULE-37 / RULE-45 / RULE-46 / RULE-47）

结构校验除正向断言（RULE-09/10/11/12 要求必需区域存在、顺序正确、组件齐备）外，还需反向核对结构化 `regions`、底部按钮与 `wireframe.ascii` 实际绘制是否互相印证。

底部操作区按钮（RULE-37）：`wireframe.ascii` 底部操作区必须按模板 `footer.buttonOrder` 绘制按钮，且按钮文案落在模板允许的标签集合内。按钮文案与语义槽位的对应关系由校验器的槽位标签集合统一登记：`previous`（上一步/上一个）、`next-or-complete`（下一步/下一个/完成/提交）、`cancel`（取消）、`confirm`（确定/确认/保存）、`close`（关闭）；日志详情抽屉按 Common Design §1.9 使用"上一个/下一个/关闭"，抽屉类页面底部按钮统一左对齐（left），弹窗类页面保持右对齐（right）。

| 场景 | 级别 | errorCode |
|---|---|---|
| 底部操作区一个模板按钮都没画（如仅画"关闭"） | error | FOOTER_ASCII_BUTTON_MISSING |
| 底部按钮出现顺序与模板 buttonOrder 不一致 | error | FOOTER_ASCII_ORDER_MISMATCH |
| 底部按钮文案不在模板允许集合（缺次要按钮在顺序正确时降为 warning） | error / warning | FOOTER_ASCII_BUTTON_MISSING |
| 底部操作区出现模板外的业务自定义按钮（如"保存并关闭"）且未声明 override | error | FOOTER_ASCII_CUSTOM_BUTTON |
| `regions[].position` 的相对顺序与 `wireframe.ascii` 中区域标签首次出现的行序不一致 | warning | WIREFRAME_REGION_ORDER_MISMATCH |
| 页面级单例控件（导出/导入/刷新/查询/重置/确定/取消等，见校验器 `SINGULAR_CONTROLS`）在 `wireframe.ascii` 中同页重复绘制 | warning | WIREFRAME_DUPLICATE_CONTROL |
| 同一内容区域（步骤条/Tab/工具栏/筛选区/分页，见校验器 `REGION_SINGLETON_KEYS`）在 `wireframe.ascii` 中被重复绘制 | warning | WIREFRAME_DUPLICATE_REGION |
| `wireframe.ascii` 内容行右边界（右竖线）错位，疑似两列结构断裂 | warning | WIREFRAME_COLUMN_ALIGNMENT |

**业务自定义底部按钮**：底部操作区允许出现模板 buttonOrder 之外的业务按钮（以业务为准），但必须通过 `templateContract.override` 声明覆盖来源；未声明即被 RULE-37 判为 `FOOTER_ASCII_CUSTOM_BUTTON` 阻断。

**模板 override 对结构校验的影响**：页面 `templateContract.override.enabled = true` 时，RULE-09/10（必需区域）、RULE-11（区域顺序）、RULE-12（必需组件）、RULE-14（表格语义）对该页自动放宽（校验器跳过对应结构断言），结构以 `templateContract.override.source` 声明的 Product Design 页面模板定义为准；RULE-20（footer 对齐）与 RULE-37（底部按钮文案/自定义按钮）本就读 override。放宽后仍须保留 `override.source` 登记，不得省略。

### 11.13 下拉选项完整性与维度保留（RULE-48）

固定选项型下拉（表单下拉、筛选下拉，以及单选/多选等枚举控件）在设计说明书中必须**逐项完整列出全部选项**，禁止用“等 / 例如 / 如：/ …”只举例，否则 Coding 阶段会照抄示例、漏掉未列出的选项。校验器对“选项/规则”（表单 `rules`）与“选项范围”（筛选 `options`）单元格做完整性校验，**列全优先于规则**：选项单元格应先列出完整选项，再补充其它规则/校验说明。除**选项值完整性**外，需求源枚举表含**分组/层级列**时还必须保留**维度**：值齐但维度被压平成单层列表，同样会导致 Coding 出不了分组/树形下拉，属本条规则职责。

**声明约定**：页面对象增加 `requirementOptionSets`，逐字段声明需求文档给出的完整选项集（与 `requirementFieldNames` 同为“声明—校验”闭环）：

```json
"requirementOptionSets": [
  {"field": "风险等级", "options": ["高", "中", "低"]},
  {"field": "处置状态", "options": ["待处置", "处置中", "已处置", "已忽略"], "source": "requirement"},
  {"field": "生效范围", "dimension": "group", "sourceColumns": ["终端组", "终端"],
   "options": ["全部终端", "终端组A", "终端1", "终端组B", "终端2"]}
]
```

- `field`：字段名（对应字段数组中的 `name`，支持精确或双向包含匹配）。
- `options`：需求文档要求的完整选项列表（数组；也兼容以 `/`、`、`、`,`、`;` 等分隔的字符串）。
- `source`：可选，选项来源标记（requirement / product-design / common-design / code / ai-fill）。
- `dimension`：可选，需求源枚举表的维度标记，取值 `flat`（默认，单层）/ `group`（分组）/ `hierarchy`（层级/树/级联）；也可直接写中文“分组 / 层级”。
- `sourceColumns`：可选，需求源枚举表的列名数组（如 `["终端组", "终端"]`）；声明 ≥2 列即视为 `group`（源表“分组列 + 值列”结构）。仅当 `dimension=group/hierarchy` 或 `sourceColumns` ≥2 列时才启用维度校验，缺省 `flat` 零负担。

**校验项**（条件式：页面声明 `requirementOptionSets` 时启用）：

| 场景 | 级别 | errorCode |
|---|---|---|
| 声明选项未全部出现在该字段表单 `rules` 或筛选 `options` 单元格 | error | REQUIRED_OPTION_MISSING |
| 声明选项集的字段未出现在页面任何字段数组 | error | OPTION_FIELD_NOT_FOUND |
| 选择类字段（component/iduxComponent 命中下拉/select/单选/多选等）选项单元格出现 等/例如/如：/… 截断指纹（未声明选项集） | warning | OPTION_TRUNCATION_MARKER |
| 选项集声明项非对象（{field, options}） | warning | OPTION_SET_INVALID |
| 选项集声明缺少 field 或 options | warning | OPTION_SET_INCOMPLETE |
| 声明了 `dimension=group/hierarchy`（或 `sourceColumns` ≥2 列）但选项单元格被压成单层列表，未保留分组/层级维度 | warning | OPTION_DIMENSION_LOST |

**维度保留的口径分工**（避免两处口径漂移）：
- **是否保留维度**属于本条规则（需求事实保全）：分组写成“组名：选项A/选项B/…”，层级写成“父级 → 子级”，或用分组标签/缩进表达；禁止压平为单层列表。
- **用什么控件承载该维度**（分组下拉、树形下拉、带搜索的树等）**不在本条规则判定**，按 RULE-54 由 Common Design widget patterns（`03-patterns/07-widget-patterns/`）判定，并把命中的判定小节锚点登记到 `codingGuide.designReferences` 且 `readLedger` 命中 `status=read`（缺依据或未精读由 RULE-54 告警）。

**选项令牌匹配**：校验按选项分隔符（`/`、`、`、`,`、`;`、换行等）拆分单元格，去掉标签前缀（如“选项：”）、括号补充（如“（默认）”）与尾部截断标记（如“低等”的“等”）后逐项归一比对，避免“指定终端”被“指定终端组”这类前缀误判。

**示例**：声明 `{"field": "生效范围", "options": ["全部终端", "指定终端组", "指定终端"]}`，但筛选字段 `options` 只写 `全部终端/指定终端组`，则 RULE-48 以 `REQUIRED_OPTION_MISSING` 阻断并指出缺失选项 `指定终端`；写成 `全部终端/指定终端组/自定义等`（未声明选项集）则触发 `OPTION_TRUNCATION_MARKER` 告警。声明 `{"field": "生效范围", "dimension": "group", "options": ["终端组A", "终端1", "终端2"]}` 但选项单元格只写 `终端组A/终端1/终端2`（压平）则触发 `OPTION_DIMENSION_LOST` 告警；写成 `终端组A：终端1/终端2` 保留维度则不告警。

### 11.14 详情页字段去重（RULE-49）

详情类页面（详情抽屉 / 下钻详情页 / 详情弹窗）顶部常有“对象摘要 / 详情概览卡片”，已展示名称、状态等关键字段；Common Design 明确这些字段不应在下方“详情描述列表”中重复展示。本校验作为兜底，避免同一字段（如启用状态）在概览卡片、基本信息描述列表等多处以不同形态重复出现。

**区域定义**：
- Zone A（概览卡片 / 对象摘要字段）：页面声明的 `detailSummaryFields` 优先；未声明时取页面级/区块 `cardFields`，以及摘要卡片型区块（`type`/`title` 命中 summary-card/object-summary/summary/profile/对象摘要/摘要卡片/摘要/概览卡片）的 `fields`/`detailFields`。注意 overview/概览 属概览内容列表，归 Zone B。
- Zone B（详情描述列表字段）：区块 `type`/`title` 命中描述列表型（overview/descriptions/description/detail/detail-content/basic-info/概览/描述列表/描述/详情/基本信息/详情信息/概要）的 `fields`/`detailFields`/`cardFields`，以及页面级 `detailFields`。

**声明约定（推荐，与 RULE-36/48 同为“声明—校验”闭环）**：页面对象增加 `detailSummaryFields`，显式声明概览卡片/对象摘要已展示的字段名数组；未声明时回退为 `cardFields` + 摘要型区块的启发式判定。

```json
"type": "详情抽屉",
"detailSummaryFields": ["策略名称", "启用状态"],
"detailDedupExempt": {"启用状态": "概览用徽标、详情需可编辑，属有意重复"}
```

**校验项**（条件式：仅详情类页面，且同时存在概览卡片/摘要字段与描述列表字段时启用）：

| 场景 | 级别 | errorCode |
|---|---|---|
| 概览卡片/对象摘要已展示字段又在详情描述列表重复出现 | warning | DETAIL_FIELD_DUPLICATE |
| 同一详情描述列表区块内字段名重复出现 | error | DETAIL_FIELD_DUPLICATED_IN_LIST |

**豁免与排除**：`excludedFields` 与页面级 `detailDedupExempt`（字段名到原因的映射，或字段名数组）中的字段不参与去重；历史/日志/记录/时间线类区块（history/timeline/audit/操作记录/变更记录/历史/日志/审计/时间线）与 `tableFields` 不参与，避免把“状态变更记录表”误判为重复。

**与 RULE-36 的关系**：概览卡片字段只需落在 Zone A（`cardFields`/摘要区块/`detailSummaryFields` 对应字段）即满足 RULE-36 字段完整性（RULE-36 统计任意字段数组），**去重不违反完整性**，无需为“防漏”而在描述列表重复。

**示例**：详情抽屉 `cardFields` 为 `[策略名称, 启用状态]`，基本信息描述列表 `detailFields` 又含 `策略名称`，则触发 `DETAIL_FIELD_DUPLICATE`；若确有需要（如状态既做概览徽标又需可编辑），写入 `detailDedupExempt` 即不再告警。

### 11.15 按钮/可点击操作表（RULE-50）

每个区块的"按钮/可点击操作"以**表格**输出，列顺序固定为：**操作 | 触发方式 | 使用组件 | 文案或字段 | Demo反馈 | 来源**。没有二次确认的操作直接写明交互行为；涉及二次确认或"局部面板"（小到不足以单独画线框图）的操作，必须在同一行写清**用什么组件**以及**对应文案或字段**。

**行字段定义**（区块 `actions` 数组元素，兼容旧的字符串写法）：

| 键 | 含义 | 必填场景 |
|---|---|---|
| `name` | 操作名称（删除/禁用/移动…） | 必填 |
| `trigger` | 触发方式/确认方式（直接生效、标准确认弹窗、弹窗+管理员密码、局部面板、打开弹窗/抽屉…） | 涉及确认/面板时必填 |
| `component` | 使用组件（确认弹窗、面板、具体组件名） | 涉及二次确认/局部面板时必填 |
| `text` | 文案（确认标题+正文，可多行） | 高影响操作必填 |
| `fields` | 面板/弹窗内的字段或组件（数组或文本，如"选择框 + 之前/之后 下拉框"） | 面板/弹窗含表单时填 |
| `feedback` | Demo 反馈/点击结果（删除后从列表移除、状态变为已禁用…） | 建议填写 |
| `impact` | 影响级别（`high`/`normal`），缺省自动识别 | 可选 |
| `confirm` | 是否二次确认（布尔），缺省按触发方式识别 | 可选 |
| `source` | 组件与文案的设计来源：`product-design` / `common-design` / `requirement` / `code` / `ai-fill` | 提供组件或文案时必填 |
| `sourceRef` | 来源可定位引用（`<文档路径>#<章节/模板条目>`） | `source` 为 product-design / common-design 时必填 |

**高影响操作的识别（自动识别 + 可配置）**：

- 自动识别：`impact: high` 或 `confirm: true`；`name` 命中默认高影响操作名或关键词即视为高影响。默认名：删除、禁用、重启、业务下线、批量处置、未保存离开；默认关键词：删除、禁用、停用、重启、下线、批量处置、批量删除、批量禁用、未保存、离开、移除、注销、清空、覆盖、解绑、提权、强制、处置、销毁、报废、重置。上述仅为示例基线。
- 可配置：spec 顶层或页面级 `actionRules` 可扩展/豁免（均为扩展语义）——`highImpactActions` 追加高影响操作名；`highImpactKeywords` 追加高影响关键词；`exempt` 指定跳过高影响校验的操作名（仍应人工确认）。

**组件与文案来源（硬约束）**：组件与文案**不得由 AI 自拟**，必须优先从 Product Design、其次从 Common Design 的 pattern 中查找；同一能力两者都定义时**以 Product Design 为准**。因此每个提供组件/文案的行都必须标注 `source`，设计库来源还须给出 `sourceRef` 锚点。

**校验项（error 阻断 / warning 提示）**：

| 场景 | 级别 | errorCode |
|---|---|---|
| 高影响操作缺少二次确认文案 | error | ACTION_CONFIRM_TEXT_MISSING |
| 操作涉及二次确认/局部面板但未写明使用组件 | warning | ACTION_COMPONENT_MISSING |
| 声明了弹窗/面板组件但既无文案也未列字段 | warning | ACTION_CONTENT_MISSING |
| 组件/文案来源缺失、标为 ai-fill、缺锚点或取值非法 | warning | ACTION_SOURCE_NOT_TRACED |
| 操作行缺少操作名称 | warning | ACTION_NAME_MISSING |

**兼容**：`actions` 仍可写字符串列表（如"查询：按条件刷新表格"），此类旧写法按单列渲染、不参与 RULE-50 校验。

**示例 A：高影响操作表**

| 操作 | 触发方式 | 使用组件 | 文案或字段 | Demo反馈 | 来源 |
|---|---|---|---|---|---|
| 删除 | 标准确认弹窗 | IxModal.confirm | 确认删除吗？<br>删除后，数据不可恢复，请谨慎操作。 | 删除成功后从列表移除 | common-design#modal |
| 禁用 | 标准确认弹窗 | IxModal.confirm | 确认禁用吗？<br>禁用后，相关业务可能受影响，请谨慎操作。 | 状态变为已禁用 | common-design#modal |
| 业务下线 | 弹窗 + 管理员密码 | 确认弹窗 + 密码输入 | 确认下线吗？<br>下线后，业务访问可能受到影响，请谨慎操作。 | 状态变为已下线或下线中 | product-design#<锚点> |
| 批量处置 | 标准确认弹窗 | IxModal.confirm | 确认执行批量处置吗？<br>将对选中的对象执行批量操作，请谨慎操作。 | 批量更新状态或提示部分成功 | common-design#modal |
| 未保存离开 | 标准确认弹窗 | IxModal.confirm | 确认离开吗？<br>当前修改未保存，离开后不会生效，请谨慎操作。 | 保存、放弃、继续编辑 | common-design#modal |

**示例 B：局部面板 + 二级弹窗（移动）**

| 操作 | 触发方式 | 使用组件 | 文案或字段 | Demo反馈 | 来源 |
|---|---|---|---|---|---|
| 移动 | 局部面板（置顶直接生效；指定位置再出弹窗） | 下拉面板 + 确认弹窗 | 字段：目标类型选择框、之前/之后 下拉框；文案：确认移动到指定位置吗？ | 置顶即时生效；指定位置确认后插入到目标项前后 | product-design#<锚点> |

### 11.16 表格区按钮位置（RULE-51）

表格区所有按钮（**批量操作**，以及**其他子功能入口按钮**，如新增/导入/导出/列设置等）必须**统一绘制在表格区左上角工具栏**，禁止绘制在表格框下方或其他区域。

**判定逻辑（warning）**：
- 定位 ascii 线框图中的表格框：取"内部含 `|` 分隔数据行"的最小嵌套盒子，记录其上/下边界行号。
- `TABLE_BUTTON_MISPLACED`：表格关联按钮关键词（批量/列设置/列配置/导入/导出/刷新/更多/排序/置顶/移动/新增/新建/设置/删除/编辑/停用/启用）出现在表格框**下边界之下**的行（分页行、底部操作区行、纯边框行除外）。
- `TABLE_ACTION_NOT_IN_TOOLBAR`：`批量`类按钮出现在表格工具栏区域之外（工具栏区域 = 紧邻表格框上方一行至表格框内部）。
- 表格页判定为"含 `|` 分隔数据行的嵌套盒子"；无表格框的 ascii（弹窗/表单等）自动跳过。

**校验项（warning 提示）**：

| 场景 | 级别 | errorCode |
|---|---|---|
| 表格关联按钮绘制在表格框下方 | warning | TABLE_BUTTON_MISPLACED |
| 批量操作按钮未置于表格区左上角工具栏 | warning | TABLE_ACTION_NOT_IN_TOOLBAR |

**示例（错误）**：

```
│ ┌──────────────┐ │
│ │ 名称 | 状态   │ │
│ └──────────────┘ │
│ [批量操作] [新增] │   <- 错误：表格按钮绘制在表格框下方
```

**示例（正确）**：

```
│ [批量操作] [新增] │   <- 正确：表格按钮置于表格区左上角工具栏
│ ┌──────────────┐ │
│ │ 名称 | 状态   │ │
│ └──────────────┘ │
```

### 11.17 需求入口落位闭环（RULE-52）

防止 PRD 明确点名的入口位置在页面拆解与线框图绘制中被静默丢失。典型场景：除对象管理页自身的"新增"按钮外，还要在另一个既有页面（如安全事件页告警列表行内操作）加入口，打开同一个配置容器，结果入口未落位、编码漏做。

**前置声明（条件式）**：只要 PRD 点名入口，就必须在 demo-spec 顶层声明 `requirementEntryPoints`（每个入口挂载点一条），范围外宿主另在顶层 `entryHosts` 登记；未声明 `requirementEntryPoints` 时本规则不启用，不产生任何校验项。字段定义见 references/01-workflow/01-output-templates.md 第 4.3 节。

**校验项**：

| 场景 | 级别 | errorCode |
|---|---|---|
| 入口挂载点缺少 host/hostScope/location/trigger/container，或 hostScope 非法 | error | ENTRY_POINT_INCOMPLETE |
| in-scope 宿主页面不存在于 `pages`，或宿主页面的 `sections` 操作 / `operations` 中未出现该触发元素与打开容器 | error | ENTRY_POINT_NOT_PLACED |
| out-of-scope 宿主未在 `entryHosts` 登记、未完成 Tier1 精读、或缺对应开发项、或开发项悬空 | error | ENTRY_HOST_UNREGISTERED |
| 宿主线框图（或 `entryHosts[].wireframe`）没有入口绘制痕迹 | warning | ENTRY_NOT_DRAWN |

**落位判定**：

- in-scope：宿主页面 `sections` 的 `actions` 行、或页面 `operations`（`open-container` 的 `targetPageId`）、或页面 JSON 文本中出现该入口的 `trigger` / `container` 之一，即视为已落位；否则 ENTRY_POINT_NOT_PLACED。
- out-of-scope：`entryHosts` 中以 `id`/`name` 命中宿主，且满足 `read=true` 或 `readTier=tier1`，且 `devItem` 非空并能在任一页面 `codingGuide.pageItems` 中找到，即视为已闭环；缺任一项即 ENTRY_HOST_UNREGISTERED。
- 绘制痕迹：宿主线框图 `ascii`（in-scope）或 `entryHosts[].wireframe`（out-of-scope）中出现 `trigger`、`container` 或"入口"字样，即视为已绘制；否则 ENTRY_NOT_DRAWN。

**示例（合法）**：

```json
{
  "requirementEntryPoints": [
    {"id": "EP01", "host": "P002", "hostScope": "in-scope", "location": "白名单列表工具栏",
     "trigger": "新增", "container": "P003", "source": "PRD F1"},
    {"id": "EP02", "host": "安全事件页", "hostScope": "out-of-scope", "location": "告警列表操作列",
     "trigger": "加入行为白名单", "container": "P003", "source": "PRD F1",
     "hostEvidence": {
       "navPath": ["安全事件", "事件详情", "告警列表"],
       "prdNavPath": ["安全事件", "事件详情", "告警列表"],
       "route": "/security/events/:id?tab=alarm-list",
       "title": "告警列表",
       "tabs": ["事件详情", "告警列表", "告警链"],
       "codeRefs": ["src/pages/security/alarm-list/index.tsx"],
       "matchedBy": ["route", "tab", "title"],
       "candidates": ["alarm-list", "alert-list"],
       "rejected": [{"candidate": "alert-list", "reason": "该页面为告警链，非告警列表"}]
     }}
  ],
  "entryHosts": [
    {"id": "安全事件页", "name": "安全事件页/告警列表", "scope": "out-of-scope",
     "read": true, "readTier": "tier1", "wireframe": "【告警列表操作列：加入行为白名单】",
     "devItem": "P003-E01"}
  ]
}
```

其中 `P003-E01` 必须存在于打开容器页面（P003）的 `codingGuide.pageItems`（`scope` 建议 `entry-point`）。

**示例（错误）**：PRD 点名"告警列表加入行为白名单"，但只声明了对象管理页自身的"新增"入口，PRD 点名的告警列表入口未出现在 `requirementEntryPoints`，或出现在其中但宿主未登记、线框图无入口 -> 触发 ENTRY_POINT_NOT_PLACED / ENTRY_HOST_UNREGISTERED / ENTRY_NOT_DRAWN。

### 11.18 页面定位证据闭环（RULE-53）

防止"定位宿主页面/复用页面时按文件名近似匹配"导致的张冠李戴。典型场景：应在"安全事件 → 事件详情 → 告警列表"Tab 加入口，AI 读到名为 `alert-list` 的文件就据此判定入口位置，而 `alert-list` 实为"告警链"页面，"告警列表"是 `alarm-list`，于是入口落到了错误的页面语义上。

**前置声明（条件式）**：声明 `requirementEntryPoints`（其中 `out-of-scope` 宿主）或顶层 `pageIdentityRefs` 时本规则启用；`in-scope` 宿主仅在显式提供 `hostEvidence` 时校验。字段定义见 references/01-workflow/01-output-templates.md 第 4.4 节。

**校验项**：

| 场景 | 级别 | errorCode |
|---|---|---|
| 缺身份证据或证据不全（`navPath` 空；代码模式缺 `route`/`codeRefs`；退化模式缺 `title` 与 `tabs`） | error | HOST_IDENTITY_UNVERIFIED |
| `matchedBy` 含文件名/目录名（filename/dir/path 等），或不含任何强锚点 | error | HOST_IDENTITY_FILENAME_ONLY |
| 存在多个形近/近义候选（`candidates` > 1）但未记录排除理由（`rejected` 为空） | warning | HOST_IDENTITY_AMBIGUOUS |
| 代码导航路径末级与 PRD 声明路径末级对不上 | error | HOST_NAVPATH_MISMATCH |

**判定要点**：

- 强锚点：`route` / `menu` / `tab` / `title` / `component` 等；文件名类（`filename`/`file`/`dir`/`path` 等）一律不作为定位依据。
- 退化模式（`identitySource: "degraded"`）：环境无代码或不完整时，以 `title`（标题/组件导出名）+ `tabs`/`navPath`（侧边栏/Tab 文案）对证，允许缺 `route`/`codeRefs`。
- 路径对证：`hostEvidence.prdNavPath` 与 `hostEvidence.navPath` 的末级须语义一致（如均为"告警列表"），否则判为疑似的张冠李戴。

**示例（合法 / 错误）**：合法证据见 11.17 示例中 EP02 的 `hostEvidence`；错误示例——`matchedBy: ["filename"]` 触发 HOST_IDENTITY_FILENAME_ONLY；`navPath` 末级为"告警链"而 `prdNavPath` 末级为"告警列表"触发 HOST_NAVPATH_MISMATCH。

### 11.19 组件形态描述（RULE-54）

防止"表格/表单字段只写组件名、未说明选用哪种形态"导致 Coding 还原不出正确外观。典型场景：`IxTag` 有多种标签样式，`IxSelect` 下拉面板按选项数量/层级有多种形态（带搜索框/支持新增/用树组件/需分组），单选/多选控件有多种形态（radio/卡片/下拉）。

**前置声明（条件式）**：字段声明了 >1 个形态候选 `formCandidates` 时本规则启用；仅一个候选或未声明的字段不校验（单形态组件零负担）。

**取值口径（两层来源，各管一段）**：
- 命名/枚举真值：形态清单与命名以已读取的 Common Design 组件映射（`common-design/references/05-components/idux-component-map.md`，按组件锚点精读）为准，本 Skill 不内置形态目录；命中匹配的 Product Design 已登记业务封装时以 Product Design 为准。
- 选择依据真值：本页该选哪一种形态，以 Common Design widget patterns（`common-design/references/03-patterns/07-widget-patterns/`）为判定依据，按"目录级索引 `#*` 定位命中控件对应文件 + 精读其判定小节"读取（避免整目录通读）；Product Design 侧 pattern 文档同等可用。
- 两层依据都必须锚点级登记到页面 `codingGuide.designReferences` 且 `readLedger` 命中 `status=read`；`index-only` 视为未读（RULE-43 阻断）。只写形态不读依据、或读了依据不登记，都会被告警。

**校验项**：

| 场景 | 级别 | errorCode |
|---|---|---|
| 字段声明了多个形态候选 `formCandidates` 但未写 `iduxComponentForm` | warning | COMPONENT_FORM_MISSING |
| `iduxComponentForm` 取值不在 `formCandidates` 内 | warning | COMPONENT_FORM_UNKNOWN |
| 声明了多形态候选，但页面未登记 Common Design 组件映射依据（或依据未精读命中） | warning | COMPONENT_FORM_SOURCE_UNREAD |
| 声明了多形态候选，但未登记 widget patterns 形态选择依据（或依据未精读命中） | warning | COMPONENT_FORM_RULE_UNREAD |

**展示**：`iduxComponentForm` 并入既有"iDux组件名称"列展示（形如 `IxTag（深色标签）`），不新增列；由生成器 `scripts/generate_demo_spec_html.py` 的 `normalize_component_rows` 拼接。

**示例**：

```json
[
  {"name": "风险等级", "display": "单标签", "iduxComponent": "IxTag", "iduxComponentForm": "深色标签", "formCandidates": ["深色标签", "描边标签", "状态标签"], "description": "高/中/低，使用红/橙/蓝标签"},
  {"name": "生效范围", "component": "下拉单选", "iduxComponent": "IxSelect", "iduxComponentForm": "下拉面板支持按名称搜索", "formCandidates": ["下拉面板支持按名称搜索", "下拉面板支持新增", "树形下拉"], "required": "是", "rules": "全部终端 / 指定终端组", "tips": "选择指定终端组时联动展示终端组多选"},
  {"name": "触发方式", "component": "单选卡片", "iduxComponent": "IxRadioGroup", "iduxComponentForm": "卡片形态", "formCandidates": ["基础 radio 形态", "卡片形态"], "required": "是", "rules": "自动/手动", "tips": ""}
]
```

**依据登记示例（两层依据 + 精读留痕）**（widget pattern 的具体文件名以 Common Design 实际目录为准，示例仅为占位；Product Design 侧同理写作 `<product-design 文档路径>#<章节锚点>`）：

```json
"codingGuide": {
  "designReferences": [
    {"source": "common-design", "ref": "common-design/references/05-components/idux-component-map.md#IxSelect"},
    {"source": "common-design", "ref": "common-design/references/03-patterns/07-widget-patterns/select-pattern.md#下拉面板形态选择"}
  ]
},
"designContext": {
  "readLedger": [
    {"ref": "common-design/references/05-components/idux-component-map.md#IxSelect", "status": "read"},
    {"ref": "common-design/references/03-patterns/07-widget-patterns/#*", "status": "index-only"},
    {"ref": "common-design/references/03-patterns/07-widget-patterns/select-pattern.md#下拉面板形态选择", "status": "read"}
  ]
}
```

错误示例：声明 `formCandidates: ["深色标签", "描边标签"]` 却未写 `iduxComponentForm` → COMPONENT_FORM_MISSING（warning）；写 `iduxComponentForm: "彩色卡片"`（不在候选内）→ COMPONENT_FORM_UNKNOWN（warning）。

### 11.20 能力发现完整性（RULE-55）

针对"Product Design 未读完就输出设计说明书"导致的典型漏读（该用 Product Design 业务组件的用成了 Common Design）：以**匹配到的 Product Design 自身声明的 `coverage`** 为真值，要求对其声明的**每一项能力**都显式判定"命中 / 未命中"，避免静默遗漏；判定为命中的能力必须已精读。

**前置声明（条件式）**：`designContext.productDesign.matched=true` 且 `coverage` 非空时本规则启用。

**结构化载体（`designContext.productDesign.capabilitySweep`）**：每项 `{ "capability": <能力名>, "decision": "hit|not-hit", "reason": <判定理由>, "appliesTo": [...], "evidenceRef": "<product-design 文档路径>#<章节锚点>" }`。

**取值口径**：能力清单来源于**当前实际加载的 Product Design**（其 Coverage / 能力声明）；本 Skill 不预置任何产品能力表或产品文档路径。控件特征（如资产/资产组选择、启禁用、数字范围、资产信息等）仅作为判定时的**辅助信号**，用于触发"是否需要复核该能力"，具体命中与否以 Product Design 声明为准。

**校验项**：

| 场景 | 级别 | errorCode |
|---|---|---|
| `coverage` 声明的某项能力在 `capabilitySweep` 中缺失，或判定非法（非 hit/not-hit） | warning | ABILITY_NOT_SWEPT |
| `capabilitySweep` 判定为 hit 的能力缺少 `evidenceRef`，或其 `evidenceRef` 未在 `readLedger` 中锚点级命中 `status=read` | warning | ABILITY_HIT_NOT_READ |

**示例**：

```json
"productDesign": {
  "matched": true,
  "skillId": "<product-design-skill-id>",
  "coverage": [
    {"capability": "component", "relation": "override", "appliesTo": ["page-table-basic"]}
  ],
  "capabilitySweep": [
    {"capability": "component", "decision": "hit", "reason": "启用资产信息业务封装组件", "appliesTo": ["page-table-basic"], "evidenceRef": "<product-design 文档路径>#资产信息"}
  ]
}
```

错误示例：`coverage` 声明能力 `component` 却无对应 `capabilitySweep` 项 → ABILITY_NOT_SWEPT（warning）；`capabilitySweep` 判定 hit 但 `evidenceRef` 指向未精读锚点 → ABILITY_HIT_NOT_READ（warning）。

### 11.21 模板 ID 一致性与覆盖兜底（RULE-56）

页面类型更名（`page-list-modal`→`list-modal` 等 6 项）后，Product Design 侧的 `coverage`/`capabilitySweep` 与页面的模板引用文本常滞后使用旧 ID，导致"既不报错也不生效"的静默漏判。本规则为此类漏判兜底。

**前置声明（条件式）**：声明顶层 `designContext`，或任一页面携带模板引用文本（`templateContract.templateSource`/`wireframe.layoutSource`）时启用。

**ID 归一（兼容识别）**：覆盖判定时旧 ID 自动归一为当前注册表 ID（`page-list-modal`→`list-modal`、`page-list-drawer`→`list-drawer`、`page-detail-drawer`→`detail-drawer`、`page-detail-log`→`log-detail-drawer`、`page-form-modal`→`form-modal`、`page-form-drawer`→`form-drawer`），保证 Product Design 声明即使仍写旧 ID，模板覆盖也照常被强制（RULE-43 生效，不静默跳过）。归一仅用于识别，不代表旧 ID 是合法产出。

**校验项**：

| 场景 | 级别 | errorCode |
|---|---|---|
| `productDesign.coverage[].appliesTo` 或 `capabilitySweep[].appliesTo` 声明了适用模板，但归一后未命中本次任何页面 | warning | TEMPLATE_COVERAGE_UNAPPLIED |
| `templateContract.templateSource`、`wireframe.layoutSource`、`restoreRequirement.components[].source` 等模板引用文本中出现已废弃旧 ID | warning | LEGACY_TEMPLATE_ID_REF |

**示例**：

```json
"designContext": {
  "productDesign": {
    "matched": true,
    "coverage": [
      {"capability": "template", "relation": "override", "appliesTo": ["page-list-drawer"]}
    ]
  }
}
```

上例页面 `templateContract.templateId=list-drawer` 时，`appliesTo` 归一后命中：该页必须 `templateBase=product` 且 `productTemplateRef` 非空（否则 RULE-43 阻断），且不产生 TEMPLATE_COVERAGE_UNAPPLIED。

错误示例：`appliesTo: ["detail-drawer"]` 但本次没有任何 `detail-drawer` 页面 → TEMPLATE_COVERAGE_UNAPPLIED（warning）；`layoutSource: "Common Design page-form-drawer"` → LEGACY_TEMPLATE_ID_REF（warning）。

### 11.22 表单单列布局闭环（RULE-57）

条件式启用：页面为**表单承载页**时启用——即模板为配置表单页（`page-form-config`）、下钻步骤条配置页（`page-form-stepper`）、表单弹窗（`form-modal`）、表单抽屉（`form-drawer`）之一，或页面含表单配置区块（sections 含 `formFields` 或区块标题/类型含"表单/配置项/录入"）。

口径（强制）：

- 表单配置项必须**单列**：每行一个配置项，label 在左、控件在右、**水平同一行**；容器形态（弹窗/抽屉/页面）不改变该口径；
- 禁止把两个及以上配置项画在同一行（含 `variants[].ascii`）；
- 表单布局真值以**已读取的 Common Design 表单规范**为准（本 Skill 不内置表单布局真值、不给表单类模板挂布局契约），结论须锚点级登记到页面 `codingGuide.designReferences` 并在 `readLedger` 命中 `status=read`；
- 控件形态（下拉面板变体、标签样式等）不在此规则内，按 11.19 / RULE-54 由 widget patterns 判定。

校验项（均 warning，不阻断出图）：

| 错误码 | 触发条件 | 期望 |
| --- | --- | --- |
| `FORM_LAYOUT_MULTI_COLUMN` | 线框 ascii（含 variants）同一行出现 >=2 个已声明表单字段 | 每行一个配置项（label 左、控件右、水平同一行） |
| `FORM_LAYOUT_LABEL_NOT_INLINE` | 某行仅有字段名且无控件占位，下一行有控件占位且无字段名 | label 与控件在同一行 |
| `FORM_LAYOUT_BASIS_UNREAD` | 未按锚点登记表单规范依据，或该依据未在 `readLedger` 命中 `status=read`（index-only 视为未精读） | `designReferences` 含表单规范锚点且 `readLedger` 为 read |

字段名来源：sections 中 `formFields`（含页面级 `formFields`），未声明 `formFields` 时不做多列判定（避免误伤非表单区块）。

依据登记示例：

```json
{
  "codingGuide": {
    "designReferences": [
      {"source": "common-design", "ref": "<Common Design 表单规范文档>#<表单布局章节>"}
    ]
  },
  "designContext": {
    "readLedger": [
      {"ref": "<Common Design 表单规范文档>#<表单布局章节>", "status": "read"}
    ]
  }
}
```

错误示例：ascii 中 `策略名称 [____]    生效范围 [请选择]`（一行两字段）→ FORM_LAYOUT_MULTI_COLUMN；ascii 中 label 独占一行、控件在下一行 → FORM_LAYOUT_LABEL_NOT_INLINE；表单弹窗未登记表单规范依据 → FORM_LAYOUT_BASIS_UNREAD。


### 11.23 详情页操作去重（RULE-58）

**目的**：详情类页面顶部概览卡片/对象摘要已承载的操作按钮（编辑/重启/删除等对象级操作），不得在底部按钮栏重复出现；底部按钮栏只保留页面级动作（关闭/上一个/下一个/取消/确定）。与 RULE-49（字段去重）同源：概览卡片已经承载的内容（字段或操作），不在同一页面的其他位置重复堆叠，避免同一动作在两处以不同形态出现、编码时重复实现。

**触发条件（条件式）**：页面声明了底部按钮栏（`footerActions` 非空），且存在**概览卡片/对象摘要区块**（区块 `type`/`title` 命中 summary-card / object-summary / 摘要卡片 / 对象摘要 / 概览卡片 等）并在该区块声明了 `actions`。两个条件任一不满足即跳过。

**判定口径**：

- 概览卡片操作取区块 `actions[]` 的操作名（`name`/`action`/`label`/`title` 任一），底部按钮栏操作取 `footerActions[]` 的操作名（`label`/`name` 任一）；
- 比较前做**同义归一**：编辑/修改/更改/维护 归一为「编辑」，重启/重新启动/启动 归一为「重启」，删除/移除/解绑 归一为「删除」，启用/开启、禁用/停用、导出、同步、复制/克隆等同理（别名词表见 `scripts/validate_demo_spec.py` 的 `DETAIL_ACTION_ALIASES`），避免"概览卡片写编辑、底部写修改"这类同义重复被漏判；
- 命中即告警 `DETAIL_SUMMARY_ACTION_DUPLICATE`（warning，不阻断出图）。

**豁免**：

- 页面级 `detailActionDedupExempt: ["重启"]`（数组，按操作名或归一名称匹配）；
- 区块级 `excludedActions` / `actionExempt`（在概览卡片区块内声明）。

**推荐写法**：对象级操作（编辑/重启/删除/导出等）只写在概览卡片区块的 `actions`；页面级动作（关闭/上一个/下一个/取消/确定）只写在 `footerActions`。两边职责不重叠即天然通过。

**正确示例**：

```json
{
  "sections": [
    {"title": "对象摘要", "type": "summary-card",
     "cardFields": [{"name": "策略名称", "iduxComponent": "IxText"}],
     "actions": [
       {"name": "编辑", "kind": "normal", "iduxComponent": "IxButton"},
       {"name": "重启", "kind": "high-impact", "trigger": "标准确认弹窗", "text": "确认重启该策略？"}
     ]}
  ],
  "footerActions": [{"label": "关闭", "kind": "close"}]
}
```

**错误示例（会被告警）**：

```json
{
  "sections": [
    {"title": "对象摘要", "type": "summary-card",
     "actions": [{"name": "重启"}]}
  ],
  "footerActions": [{"label": "关闭", "kind": "close"}, {"label": "重启", "kind": "normal"}]
}
```

上例「重启」已在概览卡片承载，又出现在底部按钮栏 -> `DETAIL_SUMMARY_ACTION_DUPLICATE`（warning）；应从 `footerActions` 移除，或改为仅在底部承载（概览卡片不再声明该操作）。


### 11.24 复用业务组件容器闭环（RULE-59）

**目的**：需求延伸出来的弹窗/抽屉/页面若命中 Product Design 业务封装组件（或代码识别已明确知道的业务封装功能），其样式以实现代码为准，本说明书**不再单独描述该容器**——不画线框图、不写页面内容区块、不写底部操作，只在**宿主页面**用一句话交代"点击 X 打开 Y（复用 <组件名>，不单独绘制）"。原因：自绘样式与业务封装实现不一致，会误导编码者按新样式开发，破坏与业务规范的一致性（如"资产适用规则检测"弹窗本就是业务封装功能，被自绘后 AI 按新样式实现）。

**适用范围（硬约束，不可扩大）**：仅适用于**需求延伸容器**——由宿主页面的动作触发、本身可能来自 Product Design 规范默认能力的容器，`trigger` 取值限定为：`按钮点击`、`表格字段点击`、`详情字段点击`、`行操作`、`导入`、`导出`。**需求直接点名的页面（主页面）不允许复用降级**，必须完整产出线框图与页面内容说明；容器必须有位于本次范围内的宿主页面入口，独立页面（无宿主入口）声明复用会被判为范围非法。

**写法**：

```json
{
  "id": "B04",
  "name": "资产适用规则检测",
  "type": "表单弹窗",
  "reuseBusinessComponent": {
    "decision": "reuse",
    "componentRef": "product-design/references/<文档>.md#资产适用规则检测组件",
    "hostPageId": "P01",
    "trigger": "按钮点击",
    "basis": "product-design"
  },
  "wireframe": {"templateId": "form-modal", "regions": [], "ascii": ""},
  "sections": [],
  "footerActions": [],
  "codingGuide": {
    "designReferences": [
      {"source": "product-design", "ref": "product-design/references/<文档>.md#资产适用规则检测组件"}
    ],
    "pageItems": [
      {"id": "B04-C01", "scope": "reuse-business-component", "name": "资产适用规则检测",
       "mode": "reuse", "target": {"path": "product-design", "export": "AssetRuleCheckModal"},
       "requirements": ["复用业务封装组件，不单独实现"],
       "acceptanceCriteria": ["样式以业务实现为准"]}
    ]
  }
}
```

宿主页面（P01）线框或内容说明中必须同时出现**容器名称（或 ID/组件名）**与复用标记（`复用`/`不单独`/`业务封装`/`直接使用`之一），例如"点击[资产适用规则检测]打开弹窗，复用 Product Design 组件，不单独绘制"。

**依据要求（与 RULE-43/54 一致，不新建真值源）**：

- `basis: "product-design"`：`componentRef` 指向的文档必须在 `codingGuide.designReferences` 中按 `source=product-design` 锚点级登记，且在 `designContext.readLedger` 命中 `status=read`（仅 `index-only` 不算）；
- `basis: "code"`：必须填写 `codeEvidence`（形如 `src/xxx#Symbol`）；
- `basis` 只允许 `product-design` / `code`。

**校验项**：

- 声明复用却仍自绘（`wireframe.ascii`、`wireframe.regions`、区块 `formFields`/`tableFields`/`detailFields`/`cardFields`/`filterFields`、`footerActions` 任一非空）-> `REUSE_CONTAINER_OVER_DESCRIBED`（**error**，阻断出图）
- 依据不可用（未锚点级登记 / 未精读命中 / `basis=code` 缺 `codeEvidence` / `basis` 取值非法）-> `REUSE_BASIS_UNREAD`（warning）
- 宿主页面未交代复用（无线框痕迹、无复用标记）-> `REUSE_HOST_NOTE_MISSING`（warning）
- 超出适用范围（`trigger` 非法、`hostPageId` 缺失或不在本次范围、容器无宿主入口）-> `REUSE_SCOPE_INVALID`（warning）
- 反向提示：容器（templateId 含 modal/drawer）已有宿主入口且 `designReferences` 已引用 Product Design 业务组件依据，却未声明复用 -> `REUSE_CANDIDATE_UNMARKED`（warning，提示确认是否应复用而非自绘）

**豁免与保留**：声明复用的容器不参与"必需区域 / 区域顺序 / 必需组件 / 弹窗抽屉外壳与底部 / 底部对齐与按钮顺序 / 线框绘制质量 / 线框区域绘制 / 表单单列布局"校验（这类校验都建立在"该容器要按模板自绘"的前提上）；但**模板契约（`type`↔`templateId`）与容器入口落位（`ORPHAN_CONTAINER`）仍然生效**——复用容器同样必须能被宿主页面找到。

**正确示例**：上例结构即为正确写法——容器无 ascii、无区块、无底部操作，宿主页面写明复用对象，容器保留一条 `mode=reuse` 的开发项指向业务组件。

**错误示例（会阻断）**：容器声明 `decision=reuse`，却仍写出 `wireframe.ascii`（如自绘"弹窗标题/策略名称[____]/确定"）、`sections[].formFields`、`footerActions` -> `REUSE_CONTAINER_OVER_DESCRIBED`（error），并可能连带 `REUSE_HOST_NOTE_MISSING`。此时应删除自绘内容，改为在宿主页面交代复用。
