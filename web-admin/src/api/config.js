/**
 * 全局开关。
 * USE_MOCK = true  ：所有请求走本地假数据（src/api/mock.js），不需要后端也能演示
 * USE_MOCK = false ：所有请求走真实后端接口（axios -> /api/xxx）
 *
 * 后端同学把接口写好之后，把这里改成 false 就能直接联调，页面代码一行都不用改。
 */
export const USE_MOCK = true