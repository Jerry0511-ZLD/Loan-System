package com.uestc.loanapp

/**
 * 全局配置类，一个放“开关”和常量的小盒子。
 *
 * Kotlin 里用 object 声明就能得到一个“单例”，不需要再写 private 构造函数。
 *
 * 为什么要单独写一个类？因为调试时最常改的就是“连不连真后端”。
 * 只要把 [USE_MOCK] 从 true 改成 false，整个 App 就从本地假数据切成真实接口，
 * 其他代码一行都不用动。
 *
 * 关于 [BASE_URL] 里的 10.0.2.2：Android 模拟器其实是一台独立的小虚拟机，
 * 在它内部 127.0.0.1 指的是模拟器自己，而 10.0.2.2 才是“运行模拟器的那台电脑”（也就是你启动后端的电脑）。
 * 所以模拟器访问电脑上的 localhost 服务，必须写 10.0.2.2。
 * 如果用真机调试，要改成电脑在局域网中的 IP，例如 http://192.168.1.5:8080/api。
 */
object AppConfig {

    /** 后端接口地址前缀，后面拼接具体的路径，例如 /login、/products。 */
    const val BASE_URL: String = "http://10.0.2.2:8080/api"

    /** true = 使用 MockApi 里的本地假数据；false = 走 BASE_URL 的真实后端。 */
    const val USE_MOCK: Boolean = true
}