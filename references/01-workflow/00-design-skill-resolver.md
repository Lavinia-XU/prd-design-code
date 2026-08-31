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

先识别当前需求所属产品，再寻找：

- `skill_type: product-design`
- `product_id` 与当前产品一致

的 Skill。

禁止仅通过 Skill 名称中是否出现 XDR、SASE、DSP 等产品缩写判断业务 Design Skill。

没有匹配 Product Design 时，不得使用其他产品的 Product Design 作为参考；这不阻止页面拆解，也不作为待确认问题。此时继续使用 Common Design、当前代码环境和明确标记的AI补齐。仅当发现多个可能匹配的 Product Design 且无法判断选择对象时，才进入待确认问题。

产品身份必须通过 Product Design 的 metadata、product_id 或 Resolver 结果确定，不得在通用 Skill 内容中硬编码具体产线或产品名称，也不得通过产品名称缩写猜测 Product Design。

---

## 3. 读取顺序

Design Skill 的读取采用“索引优先、Reference 按需”的方式。

第一阶段只读取：

1. Design Skill 的 SKILL.md；
2. Coverage；
3. Reference Index。

禁止第一阶段直接递归读取 Design Skill 下所有 Reference。

根据当前需求识别命中的能力后，再读取对应 Reference。

### 3.1 能力识别参考框架（防漏清单）

识别“本需求命中了哪些设计能力”时，对照以下五层参考框架自查，防止静默遗漏：

| 层 | 内容 | 典型命中信号 |
|----|------|-------------|
| Theme 主题层 | 功能主题（如策略配置、规则配置、任务管理、授权管理）提供的该类需求设计框架 | 需求涉及某类固定业务功能集合，存在主题级框架可填充 |
| Template 模板层 | 页面级布局骨架 | 需求涉及新页面或页面容器 |
| Feature 业务功能层 | 固定业务功能点的用法规范 | 需求涉及产品既有功能点（如策略、任务、授权） |
| Pattern 模式层 | 可复用通用交互方案（导航结构、菜单层级、页面归属、表格表单设计、交互反馈、文案术语等） | 需求涉及导航、表格、表单、交互、状态、术语 |
| Component 组件映射表 | 基础组件用法 | 需求涉及组件选择与映射 |

约束：

- 五层是“能力识别参考框架”，不是“必须逐层读取的清单”。
- 命中才读：仅在某层存在与当前需求匹配的内容时，才读取对应 Reference。
- 未命中留痕：未命中的层在 Design Context 中记录“未命中/不适用”及原因，不产生读取。
- 禁止将五层理解为全量读取清单，禁止无差别读取 Design Skill 中全部 Reference。
- 同步规则：读取 Common Design 页面模板（Template 层）后，必须与本 Skill 的模板注册表（references/02-template-contracts/common-design-template-registry.json）对比；当 Common Design 模板定义与注册表不一致时，以 Common Design 为准，并将差异记录到 Design Context 待同步。Product Design 若声明了页面模板覆盖（override），以 Product Design 为准。

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
| 页面模板与线框图 | 按声明（override 时按 Product Design 页面模板，否则按 Common Design 页面模板） | 匹配 Product Design 页面模板文档（如 product-design 的页面模板定义）或 Common Design 页面模板文档（03-design-template/01-page-types.md） |

---

## 6. Design Context

完成 Reference 读取后，形成当前任务的 Design Context。

Design Context 至少应明确：

- 当前产品；
- 当前任务命中的设计能力；
- 每项能力对应的规则来源；
- 若存在匹配 Product Design，记录其对 Common Design 的继承关系；
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
- 所需 Reference 是否已读取；
- 若存在匹配 Product Design，inherit / extend / override 是否已解析；
- 是否存在尚未解决的规则冲突；
- 是否存在影响页面结构的待确认问题。

未完成上述检查，不进入页面拆解。
