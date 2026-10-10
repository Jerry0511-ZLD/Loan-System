import request from './request'
import { USE_MOCK } from './config'
import { mockLogin } from './mock'

/**
 * 用户 / 登录相关接口。
 * 每个函数都长这样：USE_MOCK 为真走假数据，为假走真接口。
 * 页面里只调用 login()，不关心数据是真是假。
 */

/** 登录：POST /api/login */
export function login(data) {
  if (USE_MOCK) return mockLogin(data)
  return request.post('/login', data)
}