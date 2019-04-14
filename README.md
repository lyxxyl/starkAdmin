#starkAdmin

1.将stark组件放入项目中

2.将stark加入到setting中。'stark.apps.StarkConfig'

3.在每个app中创建stark.py,删除admin.py。autodiscover_modules('stark')

4.在url.py配置stark的路由。url(r'^Stark/', site.urls)(导入site)

5.在stark.py中注册数据库表,或进行自定义数据形式。site.register(数据表名)

6.新建数据形式，类名要继承ModelStark,且注册不同。

class 类名(ModelStark):             site.register(数据表名,类名)

7.用法与admin相似。

