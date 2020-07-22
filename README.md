# wechat_gateway
企业微信网关，转发告警信息到企业微信的自定义应用

# 使用
启动监听服务
./gateway.py
# 测试
curl http://x.x.x.x:6088 -X POST -d '{"msg": "world"}' --header "Content-Type: application/json"


