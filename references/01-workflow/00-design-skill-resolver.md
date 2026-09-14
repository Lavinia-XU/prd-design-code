# Design Skill Resolver

## 1. 使用目的

本规范用于指导 prd-design-code 在设计前识别、选择和装配 Common Design，并在存在匹配项时叠加 Product Design。

Resolver 只决定设计知识来源，不负责具体页面设计。

---

## 2. Design Skill 识别

### Common Design

优先识别声明：

- `skill_type: common-design`

的 Skill。

若只有一个 Common Design，直接使用。

不得通过文件夹名称、普通关键词或 Reference 文件名称猜测多个 Common Design 的优先级。

### Product Design

先识别当前需求所属产品或需求中明确出现的产品名称，再寻找：

- `skill_type: product-design`
- 需求产品名命中其任一产品标识

的 Skill。

Product Design 通过 metadata 的 `product_id` 声明其服务的产品标识。同一产品存在多个名称（例如 AES 与 DR 为同一产品，需求资料中可能显示为 DR，但需调用 AES 的 Product Design）时，`product_id` 允许声明逗号分隔的多个标识（如 `product_id: aes, dr`），首个为主标识，其余为同一产品的别名标识；需求产品名（主名或别名）与任一标识一致（忽略大小写与空白）即判定匹配，可调用该 Product Design。禁止要求需求产品名必须与主标识一致，禁止仅因需求使用别名就判定不匹配。

禁止仅通过 Skill 名称中是否出现 XDR、SASE、DSP 等产品缩写判断业务 Design Skill；Product Design 的多标识必须以 metadata 实际声明为准，不得在未声明时把产品缩写当作其标识。

没有匹配 Product Design 时，不得使用其他产品的 Product Design 作为参考；这不阻止页面拆解，也不作为待确认问题。此时继续使用 Common Design、当前代码环境和明确标记的AI补齐。仅当发现多个可能匹配的 Product Design（含同一需求产品名命中多个 Product Design 的多标识声明）且无法判断选择对象时，才进入待确认问题。

产品身份必须通过 Product Design 的 metadata、product_id（同一产品可声明逗号分隔的多标识，需求产品名命中任一标识即视为一致）或 Resolver 结果确定，不得在通用 Skill 内容中硬编码具体产线或产品名称，也不得通过产品名称缩写猜测 Product Design。

---

## 3. 读取顺序

Design Skill 的读取采用“索引优先、Reference 按需”的方式。

第一阶段只读取：

1. Design Skill 的 SKILL.md；
2. Coverage；
3. Reference Index。

禁止第一阶段直接递归读取 Design Skill 下所有 Reference。

根据当前需求识别命中的能力后，再读取对应 Reference。

### 3.0 读取证据（readLedger）与“索引 / 原文”分级

读取必须区分两个阶段，并在 Design Context 的 `readLedger` 中留痕（结构化提交为顶层 `designContext.readLedger`）：

- 索引阶段：只读了 SKILL.md / Coverage / Reference Index，仅用于定位与命中判断；此阶段看到的文档记为 `status: index-only`。
- 精读阶段：实际读取了文档正文（含锚点章节）；记为 `status: read`。

约束：

- readLedger 必须精确到**锚点粒度**：每条为 `{ "ref": "<文档路径>#<章节/模板条目>", "status": "read|index-only" }`；已读整篇时用 `#*` 显式声明。Common Design 的路径固定（页面模板 `common-design/references/02-template/01-page-types.md`、组件映射 `common-design/references/05-components/idux-component-map.md`），可直接引用；Product Design 的目录结构随产品而异，本 Skill 不预置任何具体的 `product-design` 文档路径，其路径与章节锚点必须取自当前实际加载的 Product Design Skill（示例统一写作 `<product-design 文档路径>#<章节锚点>`）；
- 只有覆盖该锚点且 `status: read` 的条目才允许作为设计依据登记到页面 `codingGuide.designReferences`；`index-only`（只看了索引、摘要、文件名或他方转述）的条目不得作为设计依据，禁止据此下模板结构、覆盖范围、必需区域、区域顺序或 footer 契约结论；
- 引用必须**锚点级命中**：读了文档 A 的某个小节，不能作为同文档**另一未精读小节**的依据；
- 页面 `designReferences.ref` 必须为精确锚点（格式`<文档路径>#<章节/模板条目>`），并能在 `readLedger` 中锚点级命中一条 `status: read`；
- 页面命中 Product Design 声明了 extend/override 的某能力时，须在 `designReferences` 中登记 `source: product-design` 且 `ability: <能力名>` 的依据条目；
- 以上由自动校验 RULE-43 强制（见 references/01-workflow/04-demo-output-spec.md 第 11.10 节），未读引用、仅索引引用、锚点未命中、命中能力未登记依据或覆盖未落地都会阻断 HTML 生成。

### 3.1 能力识别参考框架（防漏清单）

识别“本需求命中了哪些设计能力”时，对照以下五层参考框架自查，防止静默遗漏：

| 层 | 内容 | 典型命中信号 |
|----|------|-------------|
| Theme 主题层 | 功能主题（如策略配置、规则配置、任务管理、授权管理）提供的该类需求设计框架 | 需求涉及某类固定业务功能集合，存在主题级框架可填充 |
| Template 模板层 | 页面级布局骨架 | 需求涉及新页面或页面容器 |
| Feature 业务功能层 | 固定业务功能点的用法规范 | 需求涉及产品既有功能点（如策略、任务、授权） |
| Pattern 模式层 | 可复用通用交互方案（导航结构、菜单层级、页面归属、表格表单设计、交互反馈、文案术语等） | 需求涉及导航、表格、表单、交互、状态、术语 |
| Component 组件映射表 | 基础组件用法与业务封装组件 | 需求涉及组件选择与映射；Product Design 的 Component 层可对 Common Design 通用组件做 extend/override（业务封装组件优先） |

约束：

- 五层是“能力识别参考框架”，不是“必须逐层读取的清单”。
- 命中才读：仅在某层存在与当前需求匹配的内容时，才读取对应 Reference。
- 未命中留痕：未命中的层在 Design Context 中记录“未命中/不适用”及原因，不产生读取。
- 禁止将五层理解为全量读取清单，禁止无差别读取 Design Skill 中全部 Reference。
- 同步规则：读取 Common Design 页面模板（Template 层）后，必须与本 Skill 的模板注册表（references/02-template-contracts/common-design-template-registry.json）对比；当 Common Design 模板定义与注册表不一致时，以 Common Design 为准，并将差异记录到 Design Context 待同步。Product Design 若声明了页面模板覆盖（override），以 Product Design 为准。
- 组件映射优先级：读取 Component 层时，匹配 Product Design 且其 Component 层（或 coverage 中 capability 为 `component` / `pattern` 的能力）已登记该业务封装组件时，组件名与用法以 Product Design 为准，并登记 `source=product-design` + `ability`；未登记时以 Common Design 组件映射表为准；严禁将组件名一律写死为 Common Design 通用组件。Pattern 层输出的 `component_requirements` 必须回填到页面 `componentContract.patternComponents`，并同步登记 `codingGuide.designReferences` 对应 ability 依据。

### 3.2 页面模板来源判定与登记（强制）

命中页面模板能力（Template 层）的每个页面，在绘制线框图与生成 HTML 前，必须完成该页的“页面模板来源判定”并登记，不得跳过或在生成 HTML 后才补记：

- Product Design 声明了该页页面模板 override → 页面模板结构与线框样式以 Product Design 页面模板为准；登记 `templateContract.templateBase=product`，`templateContract.productTemplateRef` 填写指向 Product Design 模板文档原文的可定位引用（格式`<文档路径>#<章节/模板条目>`），并在 `codingGuide.designReferences` 登记 product-design 来源。
- Product Design 未声明该页页面模板 override → 页面模板结构与线框样式以 Common Design 页面模板为准；登记 `templateContract.templateBase=common`。

判定与结构依据约束：

- 页面模板结构、覆盖范围、必需区域、区域顺序与 footer 契约等结论，必须由主设计者基于 Product Design / Common Design 模板文档原文精读得出；禁止仅凭 Reference Index、摘要、他方转述或文件名推断模板结构结论。
- 引用的模板文档必须可定位到原文（`<文档路径>#<章节/模板条目>`），供复核者直达原文核对；`productTemplateRef` 与 `designReferences.ref` 均须满足该格式。
- 判定结论同时写入 Design Context（见第 6 节“页面模板层覆盖判定”）与页面 JSON `templateContract`，二者一致。
- 覆盖判定必须落为可校验的结构化数据：Design Context 的 `productDesign.coverage` 记录能力关系（inherit / extend / override）与适用页面（`appliesTo` 填 templateId，为空表示全部页面）。Product Design 声明页面模板 override 且页面命中时，页面 `templateContract.templateBase` 必须为 `product` 且 `productTemplateRef` 非空，否则以 RULE-43 `TEMPLATE_OVERRIDE_NOT_APPLIED` 阻断；采用 product 模板的页面必须反向登记 `source=product-design` 依据，否则以 `TEMPLATE_SOURCE_UNREGISTERED` 阻断。

---

## 4. Coverage 解析

存在匹配 Product Design 时，其对每类设计能力使用以下三种关系：

### 继承（inherit）

产品无特殊设计方式，完全继承 Common Design。

处理方式：

只读取对应 Common Design Reference。

### 扩展（extend）

产品保留 Common Design 的通用规则，同时有产品级补充。

处理方式：

先获得 Common Design 基础规则，再叠加 Product Design 补充规则。

### 覆盖（override）

产品具有明确不同于 Common Design 的设计方式。

处理方式：

以 Product Design 规则作为该能力最终设计规则。

仅当 Product Design 明确要求参考 Common Design 某部分时，再读取对应 Common Design 细节。

页面模板能力（Template 层）的覆盖判定执行第 3.2 节流程，并按模板层判定登记，不得以能力级覆盖关系笼统替代逐页判定。

---

## 5. Reference Selection

首先根据 PRD 识别设计能力，例如：

- 导航结构
- 页面类型
- 策略管理
- 任务管理
- 表格
- 表单
- 交互
- 状态
- 术语
- 组件

若存在匹配 Product Design，则结合其 Coverage 确定知识来源；未找到匹配 Product Design 时，直接以 Common Design 为基础，并结合当前代码环境和AI补齐。

示例：

| 设计能力 | Product Design 覆盖关系 | 实际读取 |
|---|---|---|
| 导航结构 | 覆盖（override） | 产品导航设计规范 |
| 策略管理 | 扩展（extend） | 通用策略管理规范 + 产品策略管理规范 |
| 表格 | 继承（inherit） | 通用表格设计规范 |
| 表单 | 扩展（extend） | 通用表单设计规范 + 产品表单设计规范 |
| 状态 | 继承（inherit） | 通用状态设计规范 |
| 页面模板与线框图 | 按声明（override 时按 Product Design 页面模板，否则按 Common Design 页面模板） | 匹配 Product Design 页面模板文档（如 product-design 的页面模板定义）或 Common Design 页面模板文档（02-template/01-page-types.md） |

页面模板与线框图行的覆盖判定按第 3.2 节登记 `templateBase` / `productTemplateRef`，不得仅停留在“按声明”的口头判断。

---

## 6. Design Context

完成 Reference 读取后，形成当前任务的 Design Context。

Design Context 至少应明确：

- 当前产品；
- 当前任务命中的设计能力；
- 每项能力对应的规则来源（须为 readLedger 中 status: read 的已读文档，index-only 文档不作为依据）；
- 若存在匹配 Product Design，记录其对 Common Design 的继承关系（inherit / extend / override），并按能力逐项登记；
- 页面模板层覆盖判定：每类模板页 Product Design 是否声明页面模板 override、判定依据（Product Design 模板文档原文可定位引用，格式`<文档路径>#<章节/模板条目>`）、最终模板来源（product-design / common-design）；未命中页面模板能力的层记录“未命中/不适用”及原因；结构化字段为 `productDesign.coverage`（capability / relation / appliesTo）与页面 `templateContract.templateBase` / `productTemplateRef`；coverage 声明 extend / override 的**任意能力**，其适用页面必须登记同 `ability` 的 product-design 依据（RULE-43 `ABILITY_SOURCE_NOT_REGISTERED`）；
- 实际读取清单 readLedger（逐**锚点**记录 `{ "ref": "<文档路径>#<章节/模板条目>", "status": "read|index-only" }`，整篇已读用 `#*`），供 RULE-43 锚点级校验；
- 当前任务代码可用状态（verified 已核验 / partial 部分可用 / unavailable 不可用）；
- 当前已有代码中的可复用对象；
- 当前仍无明确规则的内容；
- 需要用户确认的关键冲突或业务事实。

设计阶段必须基于 Design Context 执行，不得重新任意选择其他产品设计规则。

---

## 7. 冲突处理

如果 Product Design 与 Common Design 冲突：

- 覆盖（override）→ Product Design 优先；
- 扩展（extend）→ 优先判断 Common Design 通用规则与 Product Design 补充规则是否可以同时成立；
- 继承（inherit）→ Common Design 优先。

如果当前代码与 Design Skill 冲突：

先判断代码代表历史实现，还是当前明确要求复用的实现。

不得仅因为代码已经存在，就自动推翻 Product Design。

---

## 8. 缺失处理

如果存在匹配 Product Design 但其未覆盖某项设计能力：

继续使用 Common Design。

如果 Common Design 和已匹配的 Product Design 都未覆盖：

AI可以基于当前用户目标、业务任务和已有代码进行合理补齐。

涉及真实业务规则、权限、状态流转等不可推断的信息，进入待确认问题。

---

## 9. Design Context 自检

开始页面拆解前检查：

- 当前产品是否确定；
- Common Design 是否已识别；
- 若存在匹配 Product Design，其 Coverage 是否已读取；若不存在，是否已确认按 Common Design、当前代码环境和AI补齐继续；
- 本需求命中的设计能力是否完整；
- 所需 Reference 是否已实际读取并**按锚点**登记到 readLedger（status: read），是否存在仅凭索引 / 摘要（index-only）、或引用从未精读章节作为设计依据的情况；
- 若存在匹配 Product Design，inherit / extend / override 是否已逐能力解析，且声明 extend / override 的能力是否已在对应页面登记同 `ability` 的 product-design 依据；
- 页面模板层覆盖判定是否完成并登记：每类模板页是否记录 Product Design 是否声明页面模板 override、最终模板来源与原文可定位依据；是否仅凭索引、摘要或他方转述确定模板结构、覆盖范围、必需区域、区域顺序或 footer 契约；
- 是否存在尚未解决的规则冲突；
- 是否存在影响页面结构的待确认问题。

未完成上述检查，不进入页面拆解。
